pub mod mavlink;
pub mod maze;
pub mod physics;
pub use glam::DVec3;
use mavlink::Command;
use maze::{Wall, horizontal, segment_blocked};
use physics::Physics;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

pub const VERSION: &str = "suidrone-flight-v1";
pub const HZ: u64 = 50;
pub const DT: f64 = 1. / HZ as f64;
pub const MAX_TICKS: u64 = HZ * 60 * 30;
pub const MAX_EVENTS: usize = 36_000;
pub const MAX_LEG: f64 = 10.5;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct Scenario {
    pub version: String,
    pub entrance: u8,
}
impl Default for Scenario {
    fn default() -> Self {
        Self {
            version: VERSION.into(),
            entrance: 0,
        }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Attempt {
    pub id: String,
    pub game_id: String,
    pub challenge_id: String,
    pub expires_at: u64,
    pub scenario: Scenario,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Input {
    pub tick: u64,
    pub frame: Vec<u8>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Recording {
    pub scenario: Scenario,
    pub ticks: u64,
    pub inputs: Vec<Input>,
}
impl Recording {
    pub fn new(scenario: Scenario) -> Self {
        Self {
            scenario,
            ticks: 0,
            inputs: vec![],
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Mode {
    Boot,
    Patrol,
    Offboard,
    Hold,
}
pub struct Simulation {
    pub scenario: Scenario,
    pub physics: Physics,
    pub walls: Vec<Wall>,
    pub launch: DVec3,
    pub tick: u64,
    pub mode: Mode,
    pub armed: bool,
    pub target: DVec3,
    pub hold_ticks: u64,
    pub completed: bool,
    pub takeover: bool,
    last_setpoint: u64,
    command_ticks: VecDeque<u64>,
    patrol_index: usize,
    patrol_started: u64,
    patrol: Vec<DVec3>,
}
impl Simulation {
    pub fn new(scenario: Scenario) -> Result<Self, &'static str> {
        if scenario.version != VERSION || scenario.entrance > 3 {
            return Err("unsupported scenario");
        }
        let angle = scenario.entrance as f64 * std::f64::consts::FRAC_PI_2;
        let radial = DVec3::new(angle.cos(), 0., angle.sin());
        let tangent = DVec3::new(-radial.z, 0., radial.x);
        let launch = radial * 86. + DVec3::Y * 0.95;
        let patrol = vec![
            radial * 82. - tangent * 4. + DVec3::Y * 3.2,
            radial * 76. - tangent * 4. + DVec3::Y * 3.2,
            radial * 76. + tangent * 4. + DVec3::Y * 3.2,
            radial * 82. + tangent * 4. + DVec3::Y * 3.2,
        ];
        Ok(Self {
            scenario,
            physics: Physics::new(launch),
            walls: maze::walls(),
            launch,
            tick: 0,
            mode: Mode::Boot,
            armed: false,
            target: launch,
            hold_ticks: 0,
            completed: false,
            takeover: false,
            last_setpoint: 0,
            command_ticks: VecDeque::new(),
            patrol_index: 0,
            patrol_started: 0,
            patrol,
        })
    }
    pub fn input(&mut self, frame: &[u8]) -> Result<(), &'static str> {
        let frame = mavlink::parse(frame)?;
        let Some(command) = mavlink::command(&frame)? else {
            return Ok(());
        };
        while self
            .command_ticks
            .front()
            .is_some_and(|t| self.tick.saturating_sub(*t) >= HZ)
        {
            self.command_ticks.pop_front();
        }
        if self.command_ticks.len() >= 20 {
            return Err("control rate limit 20/s");
        }
        self.command_ticks.push_back(self.tick);
        if self.completed {
            return Err("flight complete");
        }
        match command {
            Command::Arm(armed) => {
                self.armed = armed;
                if !armed {
                    self.target = self.physics.position;
                    self.mode = Mode::Hold;
                }
            }
            Command::Mode(mode) => {
                let mode = if mode > 255 { (mode >> 16) & 255 } else { mode };
                match mode {
                    6 => {
                        self.mode = Mode::Offboard;
                        self.last_setpoint = self.tick;
                    }
                    4 => {
                        self.mode = Mode::Hold;
                        self.target = self.physics.position;
                    }
                    _ => return Err("supported modes: 6 OFFBOARD, 4 HOLD"),
                }
            }
            Command::Takeoff(altitude) => {
                if !self.armed || self.mode != Mode::Offboard {
                    return Err("arm and select OFFBOARD first");
                }
                if !(1.5..=4.).contains(&altitude) {
                    return Err("takeoff altitude 1.5..4m");
                }
                self.target = self.physics.position;
                self.target.y = altitude;
                self.last_setpoint = self.tick;
            }
            Command::Position(target) => {
                if !self.armed || self.mode != Mode::Offboard {
                    return Err("arm and select OFFBOARD first");
                }
                if horizontal(target - self.physics.position) > MAX_LEG
                    || (target.y - self.physics.position.y).abs() > 3.
                {
                    return Err("setpoint increment exceeds limit");
                }
                if !(0.8..=6.).contains(&target.y) || horizontal(target) > maze::ARENA_RADIUS - 1. {
                    return Err("setpoint outside flight envelope");
                }
                if segment_blocked(self.physics.position, target, &self.walls, 0.8) {
                    return Err("setpoint crosses maze wall");
                }
                self.target = target;
                self.last_setpoint = self.tick;
                self.takeover = true;
            }
        }
        Ok(())
    }
    pub fn step(&mut self) {
        if self.completed || self.tick >= MAX_TICKS {
            return;
        }
        if self.mode == Mode::Boot && self.tick >= 110 {
            self.armed = true;
            self.target = self.launch;
            self.target.y = 3.2;
            self.mode = Mode::Patrol;
            self.patrol_started = self.tick;
        }
        if self.mode == Mode::Patrol
            && (self.target.distance(self.physics.position) < 0.7
                && self.physics.velocity.length() < 0.8
                || self.tick - self.patrol_started > 900)
        {
            self.target = self.patrol[self.patrol_index];
            self.patrol_index = (self.patrol_index + 1) % self.patrol.len();
            self.patrol_started = self.tick;
        }
        if self.mode == Mode::Offboard && self.tick.saturating_sub(self.last_setpoint) > HZ * 2 {
            self.mode = Mode::Hold;
            self.target = self.physics.position;
        }
        let motors = self.physics.controller(self.target, self.armed);
        self.physics.step(motors, DT, &self.walls, self.launch);
        self.tick += 1;
        let p = self.physics.position;
        if self.takeover
            && self.armed
            && !self.physics.collision
            && horizontal(p) <= 4.
            && (1.5..=4.).contains(&p.y)
            && self.physics.velocity.length() <= 0.5
        {
            self.hold_ticks += 1;
        } else {
            self.hold_ticks = 0;
        }
        self.completed = self.hold_ticks >= 4 * HZ;
    }
}

pub fn replay(record: &Recording, expected: &Scenario) -> Result<Simulation, &'static str> {
    if &record.scenario != expected || record.ticks > MAX_TICKS || record.inputs.len() > MAX_EVENTS
    {
        return Err("recording limits or scenario mismatch");
    }
    let mut sim = Simulation::new(expected.clone())?;
    let mut index = 0;
    for tick in 0..=record.ticks {
        let mut count = 0;
        while let Some(input) = record.inputs.get(index) {
            if input.tick < tick || input.tick > record.ticks || input.frame.len() > 280 {
                return Err("invalid input ordering or size");
            }
            if input.tick != tick {
                break;
            }
            count += 1;
            if count > 32 {
                return Err("too many inputs at one tick");
            }
            // Rejected packets have no control effect in both local and server simulation.
            let _ = sim.input(&input.frame);
            index += 1;
        }
        if tick < record.ticks {
            if sim.completed {
                return Err("recording continues after completion");
            }
            sim.step();
        }
    }
    if index != record.inputs.len() {
        return Err("input outside recording");
    }
    Ok(sim)
}

pub fn validate_completion(record: &Recording, scenario: &Scenario) -> Result<(), &'static str> {
    if replay(record, scenario)?.completed {
        Ok(())
    } else {
        Err("flight did not satisfy objective")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ground_launch_patrol_reset() {
        let mut s = Simulation::new(Scenario::default()).unwrap();
        for _ in 0..100 {
            s.step();
        }
        assert!(!s.armed);
        assert!((s.physics.position.y - 0.95).abs() < 0.1);
        for _ in 0..1500 {
            s.step();
        }
        assert!(s.armed);
        assert!(s.physics.position.y > 2.);
        assert!(s.physics.position.is_finite());
        assert_eq!(s.mode, Mode::Patrol);
        let reset = Simulation::new(s.scenario.clone()).unwrap();
        assert_eq!(reset.tick, 0);
        assert!(!reset.armed);
    }
    #[test]
    fn rejects_teleport_and_times_out() {
        let mut s = Simulation::new(Scenario::default()).unwrap();
        s.input(&mavlink::long_frame(400, 1., 0., 0)).unwrap();
        s.input(&mavlink::mode_frame(6, 1)).unwrap();
        assert!(
            s.input(&mavlink::position_frame(DVec3::new(0., 3., 0.), 2))
                .is_err()
        );
        s.input(&mavlink::position_frame(DVec3::new(86., 3., 0.), 3))
            .unwrap();
        assert!(s.takeover);
        for _ in 0..105 {
            s.step();
        }
        assert_eq!(s.mode, Mode::Hold);
    }
    #[test]
    fn deterministic_replay_and_no_claimed_completion() {
        let mut s = Simulation::new(Scenario::default()).unwrap();
        let mut r = Recording::new(s.scenario.clone());
        for tick in 0..600 {
            if tick == 5 {
                let frame = mavlink::mode_frame(4, 0);
                let _ = s.input(&frame);
                r.inputs.push(Input { tick, frame });
            }
            s.step();
        }
        r.ticks = s.tick;
        let back = replay(&r, &r.scenario).unwrap();
        assert_eq!(s.physics.position, back.physics.position);
        assert!(validate_completion(&r, &r.scenario).is_err());
        r.ticks = MAX_TICKS + 1;
        assert!(replay(&r, &r.scenario).is_err());
    }
    #[test]
    fn hold_requires_takeover_and_continuous_stability() {
        let mut s = Simulation::new(Scenario::default()).unwrap();
        s.physics.position = DVec3::new(0., 3., 0.);
        s.target = s.physics.position;
        s.armed = true;
        s.mode = Mode::Hold;
        for _ in 0..250 {
            s.step();
        }
        assert!(!s.completed);
        s.takeover = true;
        for _ in 0..300 {
            s.step();
        }
        assert!(s.completed);
    }
    #[test]
    fn swept_collision_blocks_wall() {
        let mut p = Physics::new(DVec3::new(63., 3., 5.));
        p.velocity = DVec3::new(-50., 0., 0.);
        let wall = Wall {
            a: DVec3::new(62., 0., 0.),
            b: DVec3::new(62., 0., 10.),
            height: 6.,
            thickness: 1.,
        };
        p.step([0.; 4], 0.05, &[wall], DVec3::new(86., 0.95, 0.));
        assert!(p.collision);
        assert!(p.position.x > 62.);
    }
}
