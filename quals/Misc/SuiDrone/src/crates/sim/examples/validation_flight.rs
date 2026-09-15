//! Organizer acceptance fixture, deliberately excluded from the player release.
//! Derives its graph from the same visible maze; no route is embedded in the game.
use std::{collections::VecDeque, path::PathBuf};
use suidrone_sim::{
    Attempt, DVec3, Input, MAX_TICKS, Recording, Scenario, Simulation, mavlink,
    maze::{closest, horizontal, segment_blocked},
};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let scenario = if let Some(path) = args.get(1) {
        serde_json::from_slice::<Attempt>(&std::fs::read(path).unwrap())
            .unwrap()
            .scenario
    } else {
        Scenario::default()
    };
    let mut sim = Simulation::new(scenario.clone()).unwrap();
    let mut record = Recording::new(scenario);
    // A one-metre public survey grid used only to drive organizer regression tests.
    const SIDE: usize = 191;
    const ORIGIN: i32 = 95;
    let pos = |i: usize| {
        DVec3::new(
            (i % SIDE) as f64 - ORIGIN as f64,
            3.2,
            (i / SIDE) as f64 - ORIGIN as f64,
        )
    };
    let index = |p: DVec3| {
        ((p.z.round() as i32 + ORIGIN) as usize) * SIDE + (p.x.round() as i32 + ORIGIN) as usize
    };
    let open: Vec<bool> = (0..SIDE * SIDE)
        .map(|i| {
            sim.walls
                .iter()
                .all(|w| horizontal(pos(i) - closest(pos(i), w.a, w.b)) > w.thickness / 2. + 1.65)
        })
        .collect();
    let start = index(sim.launch);
    let goal = index(DVec3::ZERO);
    let mut previous = vec![usize::MAX; SIDE * SIDE];
    let mut queue = VecDeque::from([start]);
    previous[start] = start;
    while let Some(i) = queue.pop_front() {
        if i == goal {
            break;
        }
        for (dx, dz) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
            let x = i % SIDE;
            let z = i / SIDE;
            let nx = x as i32 + dx;
            let nz = z as i32 + dz;
            if nx < 0 || nz < 0 || nx >= SIDE as i32 || nz >= SIDE as i32 {
                continue;
            }
            let next = nz as usize * SIDE + nx as usize;
            if open[next] && previous[next] == usize::MAX {
                previous[next] = i;
                queue.push_back(next);
            }
        }
    }
    assert_ne!(previous[goal], usize::MAX, "maze remains reachable");
    let mut route = vec![goal];
    while *route.last().unwrap() != start {
        route.push(previous[*route.last().unwrap()]);
    }
    route.reverse();
    let mut waypoints = vec![pos(start)];
    let mut i = 0;
    while i < route.len() - 1 {
        let mut end = i + 1;
        while end + 1 < route.len()
            && horizontal(pos(route[end + 1]) - pos(route[i])) < 5.5
            && !segment_blocked(pos(route[i]), pos(route[end + 1]), &sim.walls, 1.65)
        {
            end += 1;
        }
        waypoints.push(pos(route[end]));
        i = end;
    }
    let send = |sim: &mut Simulation, record: &mut Recording, frame: Vec<u8>| {
        sim.input(&frame).expect("valid organizer command");
        record.inputs.push(Input {
            tick: sim.tick,
            frame,
        });
    };
    send(&mut sim, &mut record, mavlink::long_frame(400, 1., 0., 0));
    send(&mut sim, &mut record, mavlink::mode_frame(6, 1));
    for target in waypoints {
        let start_tick = sim.tick;
        loop {
            if sim.tick.is_multiple_of(10) {
                let sequence = (sim.tick % 255) as u8;
                send(
                    &mut sim,
                    &mut record,
                    mavlink::position_frame(target, sequence),
                );
            }
            sim.step();
            if sim.completed {
                break;
            }
            if sim.physics.position.distance(target) < 0.30 && sim.physics.velocity.length() < 0.28
            {
                break;
            }
            assert!(
                sim.tick - start_tick < 2500,
                "stalled at {:?}, target {:?}",
                sim.physics.position,
                target
            );
        }
    }
    while !sim.completed && sim.tick < MAX_TICKS {
        if sim.tick.is_multiple_of(10) {
            send(
                &mut sim,
                &mut record,
                mavlink::position_frame(DVec3::new(0., 3.2, 0.), 0),
            );
        }
        sim.step();
    }
    assert!(sim.completed);
    record.ticks = sim.tick;
    suidrone_sim::validate_completion(&record, &record.scenario).expect("server replay agrees");
    let path = args
        .get(2)
        .map(PathBuf::from)
        .unwrap_or_else(|| std::env::temp_dir().join("suidrone-validation-flight.json"));
    std::fs::write(&path, serde_json::to_vec(&record).unwrap()).unwrap();
    println!(
        "Validated {} ticks, {} MAVLink inputs; {}",
        record.ticks,
        record.inputs.len(),
        path.display()
    );
}
