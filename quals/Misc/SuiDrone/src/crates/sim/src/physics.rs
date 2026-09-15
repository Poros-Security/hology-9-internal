use crate::maze::{ARENA_RADIUS, Wall, closest, horizontal};
use glam::{DQuat, DVec3};

#[derive(Clone, Debug)]
pub struct Physics {
    pub position: DVec3,
    pub velocity: DVec3,
    pub orientation: DQuat,
    pub angular_velocity: DVec3,
    pub motors: [f64; 4],
    pub collision: bool,
}

impl Physics {
    pub fn new(position: DVec3) -> Self {
        Self {
            position,
            velocity: DVec3::ZERO,
            orientation: DQuat::IDENTITY,
            angular_velocity: DVec3::ZERO,
            motors: [0.; 4],
            collision: false,
        }
    }

    // Port of the previous embedded controller. Units and X-frame motor order are preserved.
    pub fn controller(&self, target: DVec3, armed: bool) -> [f64; 4] {
        if !armed {
            return [0.; 4];
        }
        let error = target - self.position;
        let ax = (error.x * 0.45 - self.velocity.x * 0.7).clamp(-2.8, 2.8);
        let az = (error.z * 0.45 - self.velocity.z * 0.7).clamp(-2.8, 2.8);
        let up = self.orientation * DVec3::Y;
        let roll = ((az / 9.80665).clamp(-0.28, 0.28) - up.z.clamp(-1., 1.).asin()) * 0.75
            - self.angular_velocity.x * 0.13;
        let pitch = ((-ax / 9.80665).clamp(-0.28, 0.28) - (-up.x).clamp(-1., 1.).asin()) * 0.75
            - self.angular_velocity.z * 0.13;
        let r = roll.clamp(-0.10, 0.10);
        let p = pitch.clamp(-0.10, 0.10);
        let y = (-self.angular_velocity.y * 0.05).clamp(-0.04, 0.04);
        let v = (0.735 + error.y * 0.055 - self.velocity.y * 0.095).clamp(0.36, 0.90);
        [v - r - p + y, v + r - p - y, v + r + p + y, v - r + p - y].map(|x| x.clamp(0., 1.))
    }

    pub fn step(&mut self, outputs: [f64; 4], dt: f64, walls: &[Wall], launch: DVec3) {
        let previous = self.position;
        self.collision = false;
        for (motor, output) in self.motors.iter_mut().zip(outputs) {
            *motor += (output - *motor) * (dt / 0.08).clamp(0., 1.);
        }
        let t = self.motors.map(|x| x * x * 7.2);
        let up = self.orientation * DVec3::Y;
        let ground_effect = if self.position.y > 0. && self.position.y < 1.2 {
            1. + 0.12 * (1.2 - self.position.y) / 1.2
        } else {
            1.
        };
        let air = self.velocity - DVec3::new(0.25, 0., -0.1);
        let force = up * t.iter().sum::<f64>() * ground_effect
            - air * 0.14 * air.length().max(0.2)
            - DVec3::Y * 9.80665 * 1.6;
        self.velocity += force / 1.6 * dt;
        self.position += self.velocity * dt;
        let l = 0.23 / 2f64.sqrt();
        let torque = DVec3::new(
            l * (t[1] + t[2] - t[0] - t[3]),
            0.035 * (t[0] + t[2] - t[1] - t[3]),
            l * (t[2] + t[3] - t[0] - t[1]),
        ) - self.angular_velocity * 0.08;
        self.angular_velocity += torque / DVec3::new(0.034, 0.061, 0.034) * dt;
        let derivative = self.orientation
            * DQuat::from_xyzw(
                self.angular_velocity.x,
                self.angular_velocity.y,
                self.angular_velocity.z,
                0.,
            );
        self.orientation = (self.orientation + derivative * (0.5 * dt)).normalize();
        let support = if horizontal(self.position - launch) < 2.47 {
            0.95
        } else {
            0.15
        };
        if self.position.y <= support {
            self.position.y = support;
            if self.velocity.y < 0. {
                self.velocity.y *= -0.12;
            }
            self.velocity.x *= 0.88;
            self.velocity.z *= 0.88;
            self.angular_velocity *= 0.85;
        }
        let radial = horizontal(self.position);
        if radial > ARENA_RADIUS - 0.65 {
            let normal = DVec3::new(self.position.x, 0., self.position.z) / radial;
            self.position -= normal * (radial - (ARENA_RADIUS - 0.65));
            let out = self.velocity.dot(normal);
            if out > 0. {
                self.velocity -= normal * out * 1.4;
            }
            self.collision = true;
        }
        // Bounding boxes skip distant maze segments before swept narrow-phase tests.
        for wall in walls {
            let radius = 0.65 + wall.thickness / 2.;
            if self.position.y - 0.65 >= wall.height || self.position.y + 0.65 <= 0. {
                continue;
            }
            if previous.x.max(self.position.x) < wall.a.x.min(wall.b.x) - radius
                || previous.x.min(self.position.x) > wall.a.x.max(wall.b.x) + radius
                || previous.z.max(self.position.z) < wall.a.z.min(wall.b.z) - radius
                || previous.z.min(self.position.z) > wall.a.z.max(wall.b.z) + radius
            {
                continue;
            }
            let steps = (horizontal(self.position - previous) / 0.08).ceil().max(1.) as usize;
            for i in 0..=steps {
                let p = previous.lerp(self.position, i as f64 / steps as f64);
                let c = closest(p, wall.a, wall.b);
                if horizontal(p - c) >= radius {
                    continue;
                }
                let mut normal = (previous - closest(previous, wall.a, wall.b)).normalize_or_zero();
                if horizontal(normal) < 0.5 {
                    normal =
                        DVec3::new(-(wall.b.z - wall.a.z), 0., wall.b.x - wall.a.x).normalize();
                }
                self.position.x = c.x + normal.x * radius;
                self.position.z = c.z + normal.z * radius;
                let inward = self.velocity.dot(normal);
                if inward < 0. {
                    self.velocity -= normal * inward * 1.18;
                }
                let tangent = DVec3::new(-normal.z, 0., normal.x);
                let speed = self.velocity.dot(tangent) * 0.78;
                self.velocity.x = tangent.x * speed;
                self.velocity.z = tangent.z * speed;
                self.velocity.y *= 0.85;
                self.collision = true;
                return;
            }
        }
    }
}
