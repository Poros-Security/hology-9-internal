//! Organizer-only reference solver. It carves encrypted GIF records, emulates
//! the visual bytecode, and writes the revealed final frame as a PPM image.
use std::{env, fs};

const RECORD_TAG: u64 = 0xd6a3_7c91_52ef_b408;
const KEY: u64 = 0x7a31_d6e9_4c52_b80f;

fn crypt(data: &[u8], id: u64, nonce: u64) -> Vec<u8> {
    let mut state = KEY ^ id.rotate_left(17) ^ nonce.rotate_right(9);
    data.iter()
        .enumerate()
        .map(|(index, byte)| {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            state = state.wrapping_add(
                0x9e37_79b1_85eb_ca87u64 ^ (index as u64).wrapping_mul(0x100_0000_01b3),
            );
            byte ^ state.rotate_right(((index & 7) * 8) as u32) as u8
        })
        .collect()
}

fn asset_token(id: u64) -> u64 {
    (id ^ 0xa73c_9e51_d204_6bf8)
        .rotate_left(29)
        .wrapping_mul(0xd134_2543_de82_ef95)
}

fn interaction_key(animation: &stellar_gif::DecodedAnimation, token: u64) -> u64 {
    let mut state = token ^ 0x8f42_19d7_c6a5_e30b;
    state ^= (animation.width as u64) << 48 | (animation.height as u64) << 32;
    for frame in &animation.frames {
        let value = frame.delay_cs as u64
            | (frame.disposal as u64) << 16
            | (frame.left as u64) << 24
            | (frame.top as u64) << 40;
        state = (state ^ value).rotate_left((frame.index & 31) + 7);
        state = state.wrapping_mul(0x9e37_79b1_85eb_ca87);
        state ^= state >> 27;
    }
    state ^ (animation.frames.len() as u64).wrapping_mul(0x100_0000_01b3)
}

fn crypt_program(program: &[u8], key: u64) -> Vec<u8> {
    let mut state = key ^ 0x4d56_2f81_b39a_c7e5;
    program
        .iter()
        .enumerate()
        .map(|(index, byte)| {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            state = state.wrapping_add((index as u64).wrapping_mul(0x45d9_f3b));
            byte ^ state.rotate_right(((index & 7) * 8) as u32) as u8
        })
        .collect()
}

fn open_record(data: &[u8], start: usize) -> Option<(Vec<u8>, Vec<u8>, u64)> {
    let header = data.get(start..start + 40)?;
    if u64::from_le_bytes(header[..8].try_into().ok()?) != RECORD_TAG || header[8] != 3 {
        return None;
    }
    let id = u64::from_le_bytes(header[12..20].try_into().ok()?);
    let nonce = u64::from_le_bytes(header[20..28].try_into().ok()?);
    let length = u32::from_le_bytes(header[28..32].try_into().ok()?) as usize;
    let checksum = u32::from_le_bytes(header[32..36].try_into().ok()?);
    let program_len = u16::from_le_bytes(header[36..38].try_into().ok()?) as usize;
    let program = data.get(start + 40..start + 40 + program_len)?.to_vec();
    let cipher = data.get(start + 40 + program_len..start + 40 + program_len + length)?;
    let gif = crypt(cipher, id, nonce);
    (crc32fast::hash(&gif) == checksum
        && (gif.starts_with(b"GIF87a") || gif.starts_with(b"GIF89a")))
    .then_some((gif, program, asset_token(id)))
}

fn read_u32(code: &[u8], pc: &mut usize) -> Result<u32, &'static str> {
    let value = u32::from_le_bytes(
        code.get(*pc..*pc + 4)
            .ok_or("truncated immediate")?
            .try_into()
            .unwrap(),
    );
    *pc += 4;
    Ok(value)
}

fn emulate(code: &[u8], animation: &mut stellar_gif::DecodedAnimation) -> Result<(), &'static str> {
    let mut r = [0u32; 8];
    let mut pc = 0usize;
    let mut fuel = 2_000_000usize;
    loop {
        fuel = fuel.checked_sub(1).ok_or("fuel exhausted")?;
        let op = *code.get(pc).ok_or("pc outside program")?;
        pc += 1;
        match op {
            0x00 => return Ok(()),
            0x10 => {
                let reg = *code.get(pc).ok_or("missing register")? as usize;
                pc += 1;
                r[reg] = read_u32(code, &mut pc)?;
            }
            0x20 => {
                let reg = *code.get(pc).ok_or("missing register")? as usize;
                pc += 1;
                r[reg] ^= r[reg] << 13;
                r[reg] ^= r[reg] >> 17;
                r[reg] ^= r[reg] << 5;
            }
            0x30 => {
                let cursor_reg = code[pc] as usize;
                let state_reg = code[pc + 1] as usize;
                pc += 2;
                let cursor = r[cursor_reg] as usize;
                let x = r[3] as usize + cursor % r[5] as usize;
                let y = r[4] as usize + cursor / r[5] as usize;
                let offset = (y * animation.width as usize + x) * 4;
                let frame = animation.frames.last_mut().ok_or("missing frame")?;
                let lit = (frame.rgba[offset] & 1) ^ (r[state_reg] as u8 & 1) != 0;
                frame.rgba[offset..offset + 4].copy_from_slice(if lit {
                    &[91, 221, 255, 255]
                } else {
                    &[2, 7, 24, 255]
                });
            }
            0x40 => {
                let reg = code[pc] as usize;
                pc += 1;
                r[reg] = r[reg].wrapping_add(read_u32(code, &mut pc)?);
            }
            0x50 => {
                let lhs = code[pc] as usize;
                let rhs = code[pc + 1] as usize;
                let jump = i16::from_le_bytes([code[pc + 2], code[pc + 3]]);
                pc += 4;
                if r[lhs] < r[rhs] {
                    pc = pc
                        .checked_add_signed(jump as isize)
                        .ok_or("invalid branch")?;
                }
            }
            _ => return Err("unknown opcode"),
        }
    }
}

fn write_ppm(
    path: &str,
    animation: &stellar_gif::DecodedAnimation,
) -> Result<(), Box<dyn std::error::Error>> {
    let frame = animation.frames.last().ok_or("no decoded frames")?;
    let mut output = format!("P6\n{} {}\n255\n", animation.width, animation.height).into_bytes();
    output.extend(
        frame
            .rgba
            .chunks_exact(4)
            .flat_map(|pixel| [pixel[0], pixel[1], pixel[2]]),
    );
    fs::write(path, output)?;
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input = env::args()
        .nth(1)
        .ok_or("usage: author-solver STELLAR [revealed.ppm]")?;
    let output = env::args().nth(2).unwrap_or_else(|| "revealed.ppm".into());
    let data = fs::read(input)?;
    for start in 0..data.len().saturating_sub(40) {
        if let Some((gif, sealed_program, token)) = open_record(&data, start) {
            if sealed_program.len() <= 1 {
                continue;
            }
            let mut animation = stellar_gif::decode(&gif)?;
            let program = crypt_program(&sealed_program, interaction_key(&animation, token));
            emulate(&program, &mut animation)?;
            write_ppm(&output, &animation)?;
            println!("wrote revealed flag frame to {output}");
            return Ok(());
        }
    }
    Err("no visual-program carrier found".into())
}
