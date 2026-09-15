//! Documented common.xml subset. Both MAVLink 1 and unsigned MAVLink 2 use X25 + CRC_EXTRA.
//! This fictional vehicle deliberately accepts unsigned local control traffic.
use glam::DVec3;

pub const SYSTEM_ID: u8 = 42;
pub const COMPONENT_ID: u8 = 1;

#[derive(Clone, Debug, PartialEq)]
pub enum Command {
    Arm(bool),
    Mode(u32),
    Takeoff(f64),
    Position(DVec3),
}
#[derive(Debug)]
pub struct Frame {
    pub id: u32,
    pub payload: Vec<u8>,
}

fn definition(id: u32) -> Option<(usize, usize, u8)> {
    Some(match id {
        0 => (9, 9, 50),
        11 => (6, 6, 89),
        32 => (28, 28, 185),
        76 => (33, 33, 152),
        77 => (3, 10, 143),
        84 => (53, 53, 143),
        85 => (51, 51, 140),
        253 => (51, 54, 83),
        _ => return None,
    })
}
fn accumulate(crc: &mut u16, byte: u8) {
    let mut tmp = byte ^ (*crc as u8);
    tmp ^= tmp << 4;
    *crc = (*crc >> 8) ^ ((tmp as u16) << 8) ^ ((tmp as u16) << 3) ^ ((tmp as u16) >> 4);
}
fn checksum(bytes: &[u8], extra: u8) -> u16 {
    let mut crc = 0xffff;
    for b in bytes {
        accumulate(&mut crc, *b);
    }
    accumulate(&mut crc, extra);
    crc
}
pub fn parse(bytes: &[u8]) -> Result<Frame, &'static str> {
    if bytes.len() < 8 {
        return Err("short MAVLink frame");
    }
    let v2 = bytes[0] == 0xfd;
    if !v2 && bytes[0] != 0xfe {
        return Err("MAVLink framing");
    }
    let header = if v2 { 10 } else { 6 };
    if bytes.len() < header + 2 {
        return Err("short MAVLink header");
    }
    if v2 && bytes[2] != 0 {
        return Err("unsupported MAVLink incompatibility flags");
    }
    let len = bytes[1] as usize;
    if bytes.len() != header + len + 2 {
        return Err("MAVLink length");
    }
    let id = if v2 {
        bytes[7] as u32 | ((bytes[8] as u32) << 8) | ((bytes[9] as u32) << 16)
    } else {
        bytes[5] as u32
    };
    let (min, max, extra) = definition(id).ok_or("unsupported MAVLink message")?;
    if len > max || (!v2 && len != min) || len == 0 {
        return Err("MAVLink payload length");
    }
    let actual = u16::from_le_bytes([bytes[header + len], bytes[header + len + 1]]);
    if checksum(&bytes[1..header + len], extra) != actual {
        return Err("MAVLink checksum");
    }
    let mut payload = vec![0; max];
    payload[..len].copy_from_slice(&bytes[header..header + len]);
    Ok(Frame { id, payload })
}
pub fn encode(id: u32, mut payload: Vec<u8>, sequence: u8) -> Vec<u8> {
    let (_, _, extra) = definition(id).expect("internal supported message");
    while payload.len() > 1 && payload.last() == Some(&0) {
        payload.pop();
    }
    let mut out = vec![
        0xfd,
        payload.len() as u8,
        0,
        0,
        sequence,
        SYSTEM_ID,
        COMPONENT_ID,
        id as u8,
        (id >> 8) as u8,
        (id >> 16) as u8,
    ];
    out.extend(payload);
    let crc = checksum(&out[1..], extra);
    out.extend(crc.to_le_bytes());
    out
}
fn f32_at(p: &[u8], i: usize) -> f64 {
    f32::from_le_bytes(p[i..i + 4].try_into().unwrap()) as f64
}
fn addressed(system: u8, component: u8) -> bool {
    (system == 0 || system == SYSTEM_ID) && (component == 0 || component == COMPONENT_ID)
}
pub fn command(frame: &Frame) -> Result<Option<Command>, &'static str> {
    let p = &frame.payload;
    match frame.id {
        0 => Ok(None),
        11 => {
            if !addressed(p[4], COMPONENT_ID) {
                return Err("wrong target");
            }
            if p[5] & 1 == 0 {
                return Err("custom mode flag required");
            }
            Ok(Some(Command::Mode(u32::from_le_bytes(
                p[0..4].try_into().unwrap(),
            ))))
        }
        76 => {
            if !addressed(p[30], p[31]) {
                return Err("wrong target");
            }
            if (0..7).any(|i| !f32_at(p, i * 4).is_finite()) {
                return Err("nonfinite command");
            }
            match u16::from_le_bytes([p[28], p[29]]) {
                400 if f32_at(p, 0) == 0. || f32_at(p, 0) == 1. => {
                    Ok(Some(Command::Arm(f32_at(p, 0) == 1.)))
                }
                176 if f32_at(p, 0) as u8 & 1 != 0 => {
                    let value = f32_at(p, 4);
                    if value < 0. || value.fract() != 0. || value > u32::MAX as f64 {
                        return Err("invalid mode");
                    }
                    Ok(Some(Command::Mode(value as u32)))
                }
                22 => Ok(Some(Command::Takeoff(f32_at(p, 24)))),
                _ => Err("unsupported COMMAND_LONG"),
            }
        }
        84 => {
            if !addressed(p[50], p[51]) {
                return Err("wrong target");
            }
            if p[52] != 1 {
                return Err("LOCAL_NED frame required");
            }
            let mask = u16::from_le_bytes([p[48], p[49]]);
            // Position required; velocity, acceleration, yaw and yaw rate ignored.
            if mask != 0x0df8 {
                return Err("position-only type mask 3576 required");
            }
            let pos = DVec3::new(f32_at(p, 4), -f32_at(p, 12), f32_at(p, 8));
            if !pos.is_finite() {
                return Err("nonfinite setpoint");
            }
            Ok(Some(Command::Position(pos)))
        }
        _ => Err("not a control message"),
    }
}
pub fn put_float(payload: &mut [u8], offset: usize, value: f64) {
    payload[offset..offset + 4].copy_from_slice(&(value as f32).to_le_bytes());
}
pub fn position_frame(target: DVec3, seq: u8) -> Vec<u8> {
    let mut p = vec![0; 53];
    put_float(&mut p, 4, target.x);
    put_float(&mut p, 8, target.z);
    put_float(&mut p, 12, -target.y);
    p[48..50].copy_from_slice(&3576u16.to_le_bytes());
    p[50] = SYSTEM_ID;
    p[51] = COMPONENT_ID;
    p[52] = 1;
    encode(84, p, seq)
}
pub fn mode_frame(mode: u32, seq: u8) -> Vec<u8> {
    let mut p = vec![0; 6];
    p[0..4].copy_from_slice(&mode.to_le_bytes());
    p[4] = SYSTEM_ID;
    p[5] = 1;
    encode(11, p, seq)
}
pub fn long_frame(id: u16, param1: f64, param7: f64, seq: u8) -> Vec<u8> {
    let mut p = vec![0; 33];
    put_float(&mut p, 0, param1);
    put_float(&mut p, 24, param7);
    p[28..30].copy_from_slice(&id.to_le_bytes());
    p[30] = SYSTEM_ID;
    p[31] = COMPONENT_ID;
    encode(76, p, seq)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn truncated_v2_and_crc() {
        let bytes = position_frame(DVec3::new(4., 3., -2.), 0);
        assert_eq!(
            command(&parse(&bytes).unwrap()),
            Ok(Some(Command::Position(DVec3::new(4., 3., -2.))))
        );
        for i in 0..bytes.len() {
            let mut bad = bytes.clone();
            bad[i] ^= 0x40;
            assert!(parse(&bad).is_err());
        }
        for n in 0..bytes.len() {
            assert!(parse(&bytes[..n]).is_err());
        }
    }
    #[test]
    fn rejects_nan_wrong_frame_mask_and_address() {
        for (index, value) in [(50, 99), (51, 99), (52, 8), (48, 0)] {
            let mut frame = parse(&position_frame(DVec3::ZERO, 0)).unwrap();
            frame.payload[index] = value;
            assert!(command(&frame).is_err());
        }
        assert!(command(&parse(&position_frame(DVec3::splat(f64::NAN), 0)).unwrap()).is_err());
    }
    #[test]
    fn malformed_datagrams_never_panic() {
        let mut seed = 0x139bad_u64;
        for n in 0..10_000 {
            let mut bytes = vec![0; n % 300];
            for b in &mut bytes {
                seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
                *b = (seed >> 32) as u8;
            }
            if let Ok(frame) = parse(&bytes) {
                let _ = command(&frame);
            }
        }
    }
}
