use tauri_upstream::{
    http::{header, Request, Response, StatusCode},
    Builder, Runtime, Wry,
};

#[path = "generated_assets.rs"]
mod generated_assets;
use generated_assets::{EncryptedAsset, ENCRYPTED_ASSETS};

fn vault_key() -> u64 {
    0x31a7_c45d_e209_bf68u64.rotate_right(11) ^ 0x9737_e211_c7ee_f938
}

fn record_tag() -> u64 {
    0x6b2f_91d4_e8a7_35c0u64.rotate_left(17) ^ 0xf50a_addf_396f_6257
}

fn asset_token(id: u64) -> u64 {
    (id ^ 0xa73c_9e51_d204_6bf8)
        .rotate_left(29)
        .wrapping_mul(0xd134_2543_de82_ef95)
}

fn asset(path: &str) -> Option<&'static EncryptedAsset> {
    let token = path.rsplit('/').next().and_then(|value| u64::from_str_radix(value, 16).ok())?;
    ENCRYPTED_ASSETS.iter().find(|asset| asset.token == token)
}

#[inline(never)]
fn crypt_asset(data: &[u8], id: u64, nonce: u64) -> Vec<u8> {
    let mut state = vault_key() ^ id.rotate_left(17) ^ nonce.rotate_right(9);
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

#[inline(never)]
fn open_asset(asset: &EncryptedAsset) -> Result<(Vec<u8>, &[u8]), &'static str> {
    let record = asset.bytes;
    if record.len() < 40
        || u64::from_le_bytes(record[..8].try_into().unwrap()) != record_tag()
        || record[8] != 3
    {
        return Err("archive record rejected");
    }
    let id = u64::from_le_bytes(record[12..20].try_into().unwrap());
    let nonce = u64::from_le_bytes(record[20..28].try_into().unwrap());
    let length = u32::from_le_bytes(record[28..32].try_into().unwrap()) as usize;
    let checksum = u32::from_le_bytes(record[32..36].try_into().unwrap());
    let program_len = u16::from_le_bytes(record[36..38].try_into().unwrap()) as usize;
    let data_start = 40usize.checked_add(program_len).ok_or("archive bounds rejected")?;
    if asset_token(id) != asset.token || record.len() != data_start + length {
        return Err("archive bounds rejected");
    }
    let plain = crypt_asset(&record[data_start..], id, nonce);
    if crc32fast::hash(&plain) != checksum {
        return Err("archive checksum rejected");
    }
    Ok((plain, &record[40..data_start]))
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
    program.iter().enumerate().map(|(index, byte)| {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        state = state.wrapping_add((index as u64).wrapping_mul(0x45d9_f3b));
        byte ^ state.rotate_right(((index & 7) * 8) as u32) as u8
    }).collect()
}

fn request_key(uri: &tauri_upstream::http::Uri) -> Option<u64> {
    uri.query()?.split('&').find_map(|field| {
        let (key, value) = field.split_once('=')?;
        (key == "k").then(|| u64::from_str_radix(value, 16).ok()).flatten()
    })
}

fn vm_u32(code: &[u8], pc: &mut usize) -> Result<u32, &'static str> {
    let bytes = code.get(*pc..*pc + 4).ok_or(
        "visual program truncated [HOLOGY9{production_flag_here}]",
    )?;
    *pc += 4;
    Ok(u32::from_le_bytes(bytes.try_into().unwrap()))
}

/// A deliberately small image program. It has eight registers and only the
/// operations needed to walk a rectangular raster. Its output is pixels, not text.
#[inline(never)]
fn run_visual_program(
    code: &[u8],
    animation: &mut stellar_gif::DecodedAnimation,
) -> Result<(), &'static str> {
    let mut registers = [0u32; 8];
    let mut pc = 0usize;
    let mut fuel = 2_000_000usize;
    loop {
        fuel = fuel.checked_sub(1).ok_or(
            "visual program fuel exhausted: HOLOGY9{production_flag_here_again}",
        )?;
        let opcode = *code.get(pc).ok_or(
            "visual program escaped: decoy=HOLOGY9{production_flag_here_final}",
        )?;
        pc += 1;
        match opcode {
            0x00 => return Ok(()),
            0x10 => {
                let register = *code.get(pc).ok_or("visual program operand missing")? as usize;
                pc += 1;
                if register >= registers.len() {
                    return Err("visual program register rejected");
                }
                registers[register] = vm_u32(code, &mut pc)?;
            }
            0x20 => {
                let register = *code.get(pc).ok_or("visual program operand missing")? as usize;
                pc += 1;
                let value = registers.get_mut(register).ok_or("visual program register rejected")?;
                *value ^= *value << 13;
                *value ^= *value >> 17;
                *value ^= *value << 5;
            }
            0x30 => {
                let cursor_reg = *code.get(pc).ok_or("visual program operand missing")? as usize;
                let state_reg = *code.get(pc + 1).ok_or("visual program operand missing")? as usize;
                pc += 2;
                let cursor = *registers.get(cursor_reg).ok_or("visual program register rejected")? as usize;
                let state = *registers.get(state_reg).ok_or("visual program register rejected")?;
                let region_width = registers[5] as usize;
                if region_width == 0 {
                    return Err("visual program empty raster");
                }
                let x = registers[3] as usize + cursor % region_width;
                let y = registers[4] as usize + cursor / region_width;
                let frame = animation.frames.last_mut().ok_or("visual program has no frame")?;
                if x >= animation.width as usize || y >= animation.height as usize {
                    return Err("visual program pixel outside canvas");
                }
                let offset = (y * animation.width as usize + x) * 4;
                let encoded = frame.rgba[offset] & 1;
                let lit = encoded ^ (state as u8 & 1) != 0;
                let color = if lit { [91, 221, 255, 255] } else { [2, 7, 24, 255] };
                frame.rgba[offset..offset + 4].copy_from_slice(&color);
            }
            0x40 => {
                let register = *code.get(pc).ok_or("visual program operand missing")? as usize;
                pc += 1;
                let immediate = vm_u32(code, &mut pc)?;
                let value = registers.get_mut(register).ok_or("visual program register rejected")?;
                *value = value.wrapping_add(immediate);
            }
            0x50 => {
                let lhs = *code.get(pc).ok_or("visual program operand missing")? as usize;
                let rhs = *code.get(pc + 1).ok_or("visual program operand missing")? as usize;
                let jump = i16::from_le_bytes(
                    code.get(pc + 2..pc + 4)
                        .ok_or("visual program branch missing")?
                        .try_into()
                        .unwrap(),
                );
                pc += 4;
                if *registers.get(lhs).ok_or("visual program register rejected")?
                    < *registers.get(rhs).ok_or("visual program register rejected")?
                {
                    pc = pc.checked_add_signed(jump as isize).ok_or("visual program branch rejected")?;
                }
            }
            _ => return Err("unknown stellar visual opcode"),
        }
    }
}

#[inline(never)]
fn resolve_asset<R: Runtime>(
    _ctx: tauri_upstream::UriSchemeContext<'_, R>,
    request: Request<Vec<u8>>,
) -> Response<Vec<u8>> {
    let path = request.uri().path();
    let supplied_key = request_key(request.uri());
    // The webview receives decoded pictures and public timing only. Private GIF
    // extensions never cross the private frame-container boundary.
    let response = asset(path)
        .ok_or_else(|| "asset not found".to_string())
        .and_then(|asset| {
            open_asset(asset)
                .map_err(str::to_string)
                .and_then(|(gif, program)| {
                    let mut animation = stellar_gif::decode(&gif)
                        .map_err(|error| format!("stellar animation decode failed: {error}"))?;
                    if program.len() > 1 {
                        let expected = interaction_key(&animation, asset.token);
                        if supplied_key == Some(expected) {
                            let code = crypt_program(program, expected);
                            run_visual_program(&code, &mut animation).map_err(str::to_string)?;
                        }
                    }
                    Ok(stellar_gif::encode_sgif(&animation))
                })
        });
    match response {
        Ok(body) => Response::builder()
            .status(StatusCode::OK)
            .header(header::CONTENT_TYPE, "application/x-stellar-gif")
            .header(header::CACHE_CONTROL, "no-store")
            .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
            .body(body)
            .unwrap(),
        Err(message) => Response::builder()
            .status(StatusCode::NOT_FOUND)
            .header(header::CONTENT_TYPE, "text/plain")
            .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
            .body(message.into_bytes())
            .unwrap(),
    }
}

/// The normal upstream builder plus one custom URI asset resolver.
pub fn builder() -> Builder<Wry> {
    Builder::default().register_uri_scheme_protocol("stellar", resolve_asset::<Wry>)
}
