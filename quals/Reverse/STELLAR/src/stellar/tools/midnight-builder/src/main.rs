use gif::{DisposalMethod, Encoder, Frame, Repeat};
use std::{
    borrow::Cow,
    env, fs,
    path::{Path, PathBuf},
};
use stellar_gif::decode;

const VM_HALT: u8 = 0x00;
const VM_MOVI: u8 = 0x10;
const VM_XORSHIFT: u8 = 0x20;
const VM_REVEAL: u8 = 0x30;
const VM_ADDI: u8 = 0x40;
const VM_JLT: u8 = 0x50;

const W: u16 = 320;
const H: u16 = 180;

fn palette(variant: u8) -> Vec<u8> {
    let mut p = Vec::with_capacity(768);
    for i in 0..256u16 {
        let (r, g, b) = if i == 0 {
            (2, 7, 24)
        } else if i < 151 {
            (2, 7, 24)
        } else {
            let t = (i - 150) as u8;
            (
                variant.saturating_add(t / 3),
                75u8.saturating_add(t),
                135u8.saturating_add(t),
            )
        };
        p.extend_from_slice(&[r, g, b]);
    }
    p
}

fn starfield() -> Vec<u8> {
    let mut px = vec![0u8; W as usize * H as usize];
    for y in 0..H as usize {
        for x in 0..W as usize {
            let n = ((x as u32).wrapping_mul(0x45d9f3b)
                ^ (y as u32).wrapping_mul(0x119de1f3)
                ^ ((x * y) as u32).rotate_left(11))
            .wrapping_mul(0x27d4eb2d);
            px[y * W as usize + x] = 1 + (n % 150) as u8;
        }
    }
    let mut s = 0x51ee_d123u32;
    for _ in 0..210 {
        s ^= s << 13;
        s ^= s >> 17;
        s ^= s << 5;
        let x = s as usize % W as usize;
        s = s.rotate_left(7).wrapping_add(0x9e37_79b9);
        let y = s as usize % H as usize;
        px[y * W as usize + x] = 185 + (s >> 28) as u8 * 4;
    }
    // A quiet horizon and diamond constellation make this look like a real archive loop.
    for x in 0..W as usize {
        px[145 * W as usize + x] = 7 + ((x / 9) & 7) as u8;
    }
    for d in 0..13usize {
        let x = 270 + d.min(12 - d);
        let y = 28 + d;
        if x < W as usize && y < H as usize {
            px[y * W as usize + x] = 175;
        }
    }
    px
}

fn comet_rect(f: usize, left: u16, top: u16, width: u16, height: u16) -> Vec<u8> {
    let base = starfield();
    let mut px = vec![0u8; width as usize * height as usize];
    let cx = 22 + f as isize * 5;
    let cy = height as isize / 2 + ((f as isize % 3) - 1) * 3;
    for y in 0..height as isize {
        for x in 0..width as isize {
            let dx = x - cx;
            let dy = y - cy;
            let d2 = dx * dx + dy * dy;
            let noise = ((x as u32).wrapping_mul(0x9e3779b1)
                ^ (y as u32).wrapping_mul(0x85ebca6b)
                ^ (f as u32).wrapping_mul(0x27d4eb2d))
            .rotate_left((f & 15) as u32);
            let value = if d2 < 25 {
                250
            } else if d2 < 80 {
                205
            } else if x < cx && dy.abs() <= 2 + (cx - x) / 13 && x > 2 {
                (245 - (cx - x).min(85)) as u8
            } else if noise % 19 == 0 {
                0
            } else {
                base[(top as usize + y as usize) * W as usize + left as usize + x as usize]
            };
            px[y as usize * width as usize + x as usize] = value;
        }
    }
    // keep left/top alive in optimizer-independent art generation
    if !px.is_empty() {
        px[0] = ((left as usize + top as usize) & 1) as u8 * 30;
    }
    px
}

fn midnight_bytes() -> Vec<u8> {
    let global = palette(0);
    let mut bytes = Vec::new();
    {
        let mut enc = Encoder::new(&mut bytes, W, H, &global).expect("gif encoder");
        enc.set_repeat(Repeat::Infinite).unwrap();
        let mut first = Frame::default();
        first.width = W;
        first.height = H;
        first.delay = 7;
        first.dispose = DisposalMethod::Keep;
        first.buffer = Cow::Owned(starfield());
        enc.write_frame(&first).unwrap();
        let specs = [
            (12, 45, 138, 48, 5, DisposalMethod::Previous, false),
            (50, 55, 144, 52, 9, DisposalMethod::Background, false),
            (82, 39, 156, 60, 4, DisposalMethod::Previous, true),
            (120, 60, 132, 46, 12, DisposalMethod::Keep, false),
            (148, 31, 148, 64, 6, DisposalMethod::Previous, false),
            (188, 52, 120, 50, 10, DisposalMethod::Keep, true),
            (215, 38, 100, 58, 8, DisposalMethod::Keep, false),
        ];
        for (i, &(left, top, w, h, delay, dispose, local)) in specs.iter().enumerate() {
            let mut f = Frame::default();
            f.left = left;
            f.top = top;
            f.width = w;
            f.height = h;
            f.delay = delay;
            f.dispose = dispose;
            f.transparent = Some(0);
            f.buffer = Cow::Owned(comet_rect(i + 1, left, top, w, h));
            if local {
                f.palette = Some(palette(7 + i as u8));
            }
            enc.write_frame(&f).unwrap();
        }
    }
    bytes
}

fn emit_movi(code: &mut Vec<u8>, register: u8, value: u32) {
    code.extend_from_slice(&[VM_MOVI, register]);
    code.extend_from_slice(&value.to_le_bytes());
}

fn reveal_program(x: u16, y: u16, width: u16, height: u16, seed: u32) -> Vec<u8> {
    let mut code = Vec::new();
    emit_movi(&mut code, 0, 0); // pixel cursor
    emit_movi(&mut code, 1, width as u32 * height as u32);
    emit_movi(&mut code, 2, seed);
    emit_movi(&mut code, 3, x as u32);
    emit_movi(&mut code, 4, y as u32);
    emit_movi(&mut code, 5, width as u32);
    let loop_pc = code.len();
    code.extend_from_slice(&[VM_XORSHIFT, 2]);
    code.extend_from_slice(&[VM_REVEAL, 0, 2]);
    code.extend_from_slice(&[VM_ADDI, 0]);
    code.extend_from_slice(&1u32.to_le_bytes());
    code.extend_from_slice(&[VM_JLT, 0, 1]);
    let after_jump = code.len() + 2;
    code.extend_from_slice(&((loop_pc as isize - after_jump as isize) as i16).to_le_bytes());
    code.push(VM_HALT);
    code
}

fn embed_flag_raster(gif: &[u8], flag: &str) -> (Vec<u8>, Vec<u8>) {
    let animation = decode(gif).expect("carrier GIF must decode");
    let width = animation.width;
    let height = animation.height;
    assert!(
        width >= 220 && height >= 90,
        "flag carrier must be at least 220x90"
    );
    let box_x = 12u16;
    let box_w = width - 24;
    let box_h = 52u16;
    let box_y = height - box_h - 10;
    let seed = 0x7355_1e15u32 ^ asset_id("stellar-visual-program") as u32;

    let font_bytes =
        fs::read("app/src/assets/fonts/Archivo-Variable.ttf").expect("read bundled Archivo font");
    let font = fontdue::Font::from_bytes(font_bytes, fontdue::FontSettings::default())
        .expect("parse bundled font");
    let mut size = 22.0f32;
    while flag
        .chars()
        .map(|c| font.metrics(c, size).advance_width)
        .sum::<f32>()
        > (box_w - 16) as f32
    {
        size -= 1.0;
        assert!(size >= 10.0, "flag is too long for the carrier GIF");
    }
    let advances: f32 = flag
        .chars()
        .map(|c| font.metrics(c, size).advance_width)
        .sum();
    let mut mask = vec![false; box_w as usize * box_h as usize];
    let mut pen_x = ((box_w as f32 - advances) / 2.0).max(4.0);
    for character in flag.chars() {
        let (metrics, bitmap) = font.rasterize(character, size);
        let top = (box_h as isize - metrics.height as isize) / 2;
        for gy in 0..metrics.height {
            for gx in 0..metrics.width {
                if bitmap[gy * metrics.width + gx] > 90 {
                    let px = pen_x as isize + gx as isize;
                    let py = top + gy as isize;
                    if px >= 0 && py >= 0 && px < box_w as isize && py < box_h as isize {
                        mask[py as usize * box_w as usize + px as usize] = true;
                    }
                }
            }
        }
        pen_x += metrics.advance_width;
    }

    let palette = [2, 7, 24, 8, 18, 48, 9, 18, 48, 91, 221, 255];
    let mut pixels = vec![0u8; width as usize * height as usize];
    let mut state = seed;
    for i in 0..mask.len() {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        let encoded = mask[i] ^ (state & 1 != 0);
        let x = box_x as usize + i % box_w as usize;
        let y = box_y as usize + i / box_w as usize;
        pixels[y * width as usize + x] = if encoded { 2 } else { 1 };
    }

    let mut output = Vec::new();
    {
        let mut encoder = Encoder::new(&mut output, width, height, &[2, 7, 24, 91, 221, 255])
            .expect("GIF encoder");
        encoder.set_repeat(Repeat::Infinite).unwrap();
        for decoded in &animation.frames {
            let mut rgba = decoded.rgba.clone();
            let mut frame = Frame::from_rgba_speed(width, height, &mut rgba, 10);
            frame.delay = decoded.delay_cs.max(2);
            frame.dispose = DisposalMethod::Keep;
            encoder.write_frame(&frame).unwrap();
        }
        let mut reveal = Frame::default();
        reveal.width = width;
        reveal.height = height;
        reveal.delay = 220;
        reveal.dispose = DisposalMethod::Keep;
        reveal.palette = Some(palette.to_vec());
        reveal.buffer = Cow::Owned(pixels);
        encoder.write_frame(&reveal).unwrap();
    }
    (output, reveal_program(box_x, box_y, box_w, box_h, seed))
}

fn write_sample(path: &Path, kind: usize, disposal: DisposalMethod) {
    let w = 160u16;
    let h = 90u16;
    let pal = palette((kind * 3) as u8);
    let mut out = Vec::new();
    {
        let mut e = Encoder::new(&mut out, w, h, &pal).unwrap();
        e.set_repeat(Repeat::Infinite).unwrap();
        for fno in 0..6usize {
            let mut px = vec![0u8; w as usize * h as usize];
            for y in 0..h as usize {
                for x in 0..w as usize {
                    let dx = x as isize - (20 + (fno * 21 + kind * 7) % 125) as isize;
                    let dy = y as isize - (20 + (kind * 11) % 50) as isize;
                    let ring = ((dx * dx + dy * dy) as f64).sqrt() as usize;
                    if ring < 8
                        || (kind == 2 && (x + y + fno * 4) % 31 < 2)
                        || (kind == 4 && y == (x + fno * 9) % h as usize)
                    {
                        px[y * w as usize + x] = 120 + ((x * 3 + y * 5 + kind * 17) & 127) as u8;
                    }
                }
            }
            let mut f = Frame::default();
            f.width = w;
            f.height = h;
            f.delay = (4 + fno + kind) as u16;
            f.dispose = if fno % 2 == 1 {
                disposal
            } else {
                DisposalMethod::Keep
            };
            f.buffer = Cow::Owned(px);
            e.write_frame(&f).unwrap();
        }
    }
    fs::write(path, out).unwrap();
}

const RECORD_TAG: u64 = 0xd6a3_7c91_52ef_b408;
const VAULT_KEY: u64 = 0x7a31_d6e9_4c52_b80f;

fn asset_id(name: &str) -> u64 {
    let mut hash = 0xcbf2_9ce4_8422_2325u64;
    for byte in name.bytes() {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(0x100_0000_01b3);
    }
    hash
}

fn asset_token(id: u64) -> u64 {
    (id ^ 0xa73c_9e51_d204_6bf8)
        .rotate_left(29)
        .wrapping_mul(0xd134_2543_de82_ef95)
}

fn interaction_key(gif: &[u8], token: u64) -> u64 {
    let animation = decode(gif).expect("sealed GIF must decode");
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

fn crypt_asset(data: &[u8], id: u64, nonce: u64) -> Vec<u8> {
    let mut state = VAULT_KEY ^ id.rotate_left(17) ^ nonce.rotate_right(9);
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

fn seal(name: &str, gif: &[u8], program: &[u8]) -> Vec<u8> {
    let id = asset_id(name);
    let token = asset_token(id);
    let checksum = crc32fast::hash(gif);
    let nonce = 0x5354_454c_4c41_5221u64
        ^ id.rotate_left(23)
        ^ (gif.len() as u64).rotate_right(11)
        ^ checksum as u64;
    let encrypted = crypt_asset(gif, id, nonce);
    let sealed_program = if program.len() > 1 {
        crypt_program(program, interaction_key(gif, token))
    } else {
        program.to_vec()
    };
    let mut record = Vec::with_capacity(40 + sealed_program.len() + encrypted.len());
    record.extend_from_slice(&RECORD_TAG.to_le_bytes());
    record.push(3);
    record.extend_from_slice(&[0, 0, 0]);
    record.extend_from_slice(&id.to_le_bytes());
    record.extend_from_slice(&nonce.to_le_bytes());
    record.extend_from_slice(&(gif.len() as u32).to_le_bytes());
    record.extend_from_slice(&checksum.to_le_bytes());
    record.extend_from_slice(&(sealed_program.len() as u16).to_le_bytes());
    record.extend_from_slice(&0u16.to_le_bytes());
    record.extend_from_slice(&sealed_program);
    record.extend_from_slice(&encrypted);
    record
}

fn strip_private_extensions(mut gif: Vec<u8>) -> Vec<u8> {
    for signature in [
        b"\x21\xff\x0bSTLRDATA1.0".as_slice(),
        b"\x21\xff\x0bSTLRFLAG1.0",
    ] {
        while let Some(start) = gif
            .windows(signature.len())
            .position(|window| window == signature)
        {
            let mut end = start + signature.len();
            loop {
                let size = gif[end] as usize;
                end += 1;
                if size == 0 {
                    break;
                }
                end += size;
            }
            gif.drain(start..end);
        }
    }
    gif
}

fn generate_defaults(source_dir: &Path) {
    fs::write(source_dir.join("midnight-comet.gif"), midnight_bytes()).unwrap();
    let samples = [
        ("blue-pulse.gif", DisposalMethod::Keep),
        ("comet-trail.gif", DisposalMethod::Background),
        ("diamond-spin.gif", DisposalMethod::Keep),
        ("orbit-loop.gif", DisposalMethod::Previous),
        ("starfall.gif", DisposalMethod::Background),
    ];
    for (index, (name, disposal)) in samples.iter().enumerate() {
        write_sample(&source_dir.join(name), index, *disposal);
    }
}

fn write_registries(names: &[String], flag_carrier: &str) {
    let mut rust = String::from("// @generated by midnight-builder; do not edit.\n");
    rust.push_str(
        "pub(super) struct EncryptedAsset { pub token: u64, pub bytes: &'static [u8] }\n",
    );
    rust.push_str("pub(super) static ENCRYPTED_ASSETS: &[EncryptedAsset] = &[\n");
    for name in names {
        let token = asset_token(asset_id(name));
        let vault_name = format!("{token:016x}.stlr");
        rust.push_str(&format!(
            "    EncryptedAsset {{ token: 0x{token:016x}, bytes: include_bytes!(\"../../../../app/src/assets/vault/{vault_name}\") }},\n"
        ));
    }
    rust.push_str("];\n");
    fs::write("tauri-stellar/crates/tauri/src/generated_assets.rs", rust).unwrap();

    let mut typescript = String::from("// @generated by midnight-builder; do not edit.\nexport const generatedAnimationTokens = [\n");
    for name in names {
        typescript.push_str(&format!("  \"{:016x}\",\n", asset_token(asset_id(name))));
    }
    typescript.push_str("] as const;\n");
    typescript.push_str(&format!(
        "export const generatedFlagAnimationToken = \"{:016x}\";\n",
        asset_token(asset_id(flag_carrier))
    ));
    fs::write("app/src/lib/generated-animation-index.ts", typescript).unwrap();
}

fn main() {
    let source_dir = env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("app/src/assets/gifs"));
    fs::create_dir_all(&source_dir).expect("create gif directory");
    if env::args().any(|argument| argument == "--generate-defaults") {
        generate_defaults(&source_dir);
    }
    let flag = env::var("STELLAR_FLAG").unwrap_or_else(|_| "HOLOGY9{Fake_flag_dont_submit}".into());
    let flag_carrier = env::var("STELLAR_FLAG_GIF").unwrap_or_else(|_| "midnight-comet.gif".into());
    assert!(
        flag.starts_with("HOLOGY9{") && flag.ends_with('}'),
        "invalid STELLAR_FLAG format"
    );
    let vault_dir = source_dir.parent().unwrap_or(Path::new(".")).join("vault");
    fs::create_dir_all(&vault_dir).expect("create vault directory");
    for entry in fs::read_dir(&vault_dir).unwrap() {
        let path = entry.unwrap().path();
        if path
            .extension()
            .is_some_and(|extension| extension == "stlr")
        {
            fs::remove_file(path).unwrap();
        }
    }
    let mut sources: Vec<_> = fs::read_dir(&source_dir)
        .unwrap()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.extension().is_some_and(|extension| extension == "gif"))
        .collect();
    sources.sort();
    assert!(
        !sources.is_empty(),
        "no GIF files found in {}",
        source_dir.display()
    );
    let mut names = Vec::new();
    for path in sources {
        let name = path.file_name().unwrap().to_string_lossy().into_owned();
        let clean = strip_private_extensions(fs::read(&path).unwrap());
        decode(&clean).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        let (packaged, program) = if name == flag_carrier {
            embed_flag_raster(&clean, &flag)
        } else {
            (clean, vec![VM_HALT])
        };
        decode(&packaged).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        let record = seal(&name, &packaged, &program);
        let token = asset_token(asset_id(&name));
        fs::write(vault_dir.join(format!("{token:016x}.stlr")), &record).unwrap();
        println!(
            "sealed {name}: {} GIF bytes -> {} vault bytes",
            packaged.len(),
            record.len()
        );
        names.push(name);
    }
    assert!(
        names.iter().any(|name| name == &flag_carrier),
        "STELLAR_FLAG_GIF does not name a GIF in the source directory"
    );
    write_registries(&names, &flag_carrier);
}
