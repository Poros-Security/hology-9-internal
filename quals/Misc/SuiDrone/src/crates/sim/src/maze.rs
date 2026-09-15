use glam::DVec3;
use serde::{Deserialize, Serialize};
use std::f64::consts::{PI, TAU};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Wall {
    pub a: DVec3,
    pub b: DVec3,
    pub height: f64,
    pub thickness: f64,
}

pub const MAZE_RADIUS: f64 = 64.0;
pub const ARENA_RADIUS: f64 = 104.0;

// The existing radial-maze-v1 geometry, shared by the renderer and validator.
pub fn walls() -> Vec<Wall> {
    let mut walls = Vec::new();
    let point = |r: f64, a: f64| DVec3::new(r * a.cos(), 0., r * a.sin());
    for (ring, fraction) in [1., 0.8125, 0.625, 0.4375, 0.25].into_iter().enumerate() {
        let offset = [0., PI / 8., -PI / 7., PI / 5., -PI / 4.][ring];
        let gap = [0.14, 0.14, 0.15, 0.19, 0.30][ring];
        for i in 0..176 {
            let a0 = i as f64 * TAU / 176.;
            let a1 = (i + 1) as f64 * TAU / 176.;
            let mid = (a0 + a1) / 2.;
            if (0..4).any(|q| {
                let d = mid - (q as f64 * PI / 2. + offset);
                d.sin().atan2(d.cos()).abs() < gap
            }) {
                continue;
            }
            walls.push(Wall {
                a: point(MAZE_RADIUS * fraction, a0),
                b: point(MAZE_RADIUS * fraction, a1),
                height: if ring == 4 {
                    4.6
                } else if ring == 2 {
                    7.4
                } else {
                    6.2
                },
                thickness: if ring == 0 { 1. } else { 0.85 },
            });
        }
    }
    for q in 0..4 {
        let base = q as f64 * PI / 2.;
        for (angle, inner, outer, height) in [
            (0.20, 0.84, 0.94, 6.2),
            (0.49, 0.66, 0.78, 7.1),
            (-0.33, 0.48, 0.59, 5.4),
            (0.72, 0.29, 0.40, 6.8),
        ] {
            walls.push(Wall {
                a: point(MAZE_RADIUS * inner, base + angle),
                b: point(MAZE_RADIUS * outer, base + angle),
                height,
                thickness: 1.,
            });
        }
        for (angle, radius, half, height) in [
            (0.63, 0.72, 4.6, 5.6),
            (-0.18, 0.53, 3.8, 7.6),
            (0.91, 0.34, 3.1, 5.6),
        ] {
            let a = base + angle;
            let center = point(MAZE_RADIUS * radius, a);
            let tangent = DVec3::new(-a.sin(), 0., a.cos());
            walls.push(Wall {
                a: center - tangent * half,
                b: center + tangent * half,
                height,
                thickness: 0.9,
            });
        }
    }
    walls
}

pub fn horizontal(v: DVec3) -> f64 {
    v.x.hypot(v.z)
}
pub fn closest(p: DVec3, a: DVec3, b: DVec3) -> DVec3 {
    let ab = DVec3::new(b.x - a.x, 0., b.z - a.z);
    let t = ((p - a).dot(ab) / ab.length_squared().max(1e-12)).clamp(0., 1.);
    DVec3::new(a.x + ab.x * t, p.y, a.z + ab.z * t)
}

pub fn segment_blocked(a: DVec3, b: DVec3, walls: &[Wall], padding: f64) -> bool {
    // Conservative, height-independent route warning matches the existing gateway.
    let samples = (horizontal(b - a) / 0.2).ceil().max(1.) as usize;
    walls.iter().any(|w| {
        let r = w.thickness / 2. + padding;
        if a.x.max(b.x) < w.a.x.min(w.b.x) - r
            || a.x.min(b.x) > w.a.x.max(w.b.x) + r
            || a.z.max(b.z) < w.a.z.min(w.b.z) - r
            || a.z.min(b.z) > w.a.z.max(w.b.z) + r
        {
            return false;
        }
        (0..=samples).any(|i| {
            let p = a.lerp(b, i as f64 / samples as f64);
            horizontal(p - closest(p, w.a, w.b)) < r
        })
    })
}
