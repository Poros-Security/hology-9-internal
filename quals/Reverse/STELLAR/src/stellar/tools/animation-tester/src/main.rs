use std::{env, fs, path::PathBuf};
use stellar_gif::decode;
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = PathBuf::from(
        env::args()
            .nth(1)
            .ok_or("usage: animation-tester file.gif [dump-dir]")?,
    );
    let a = decode(&fs::read(&path)?)?;
    println!(
        "GIF {}x{} frames={} loop={} private-apps={} disposals={}",
        a.width,
        a.height,
        a.frames.len(),
        a.loop_count,
        a.application_extensions,
        a.disposal_operations
    );
    for f in &a.frames {
        println!("frame {:02}: rect=({},{} {}x{}) delay={}cs disposal={} palette={} interlace={} transparency={:?} lzw={{bytes:{}, max-width:{}, clears:{}, code==next:{}}}",f.index,f.left,f.top,f.width,f.height,f.delay_cs,f.disposal,if f.local_palette{"local"}else{"global"},f.interlaced,f.transparent_index,f.lzw_compressed_bytes,f.lzw_max_code_size,f.lzw_clear_codes,f.lzw_kwkwk_hits)
    }
    if let Some(dir) = env::args().nth(2) {
        fs::create_dir_all(&dir)?;
        for f in &a.frames {
            let ppm = |rgba: &[u8], w: u16, h: u16| {
                let mut p = format!("P6\n{} {}\n255\n", w, h).into_bytes();
                for q in rgba.chunks_exact(4) {
                    p.extend_from_slice(&q[..3])
                }
                p
            };
            fs::write(
                PathBuf::from(&dir).join(format!("frame-{:02}-display.ppm", f.index)),
                ppm(&f.rgba, a.width, a.height),
            )?;
            fs::write(
                PathBuf::from(&dir).join(format!("frame-{:02}-disposed.ppm", f.index)),
                ppm(&f.after_disposal_rgba, a.width, a.height),
            )?;
            if let Some(saved) = &f.saved_previous_rgba {
                fs::write(
                    PathBuf::from(&dir).join(format!("frame-{:02}-saved-region.ppm", f.index)),
                    ppm(saved, f.width, f.height),
                )?
            }
        }
    }
    Ok(())
}
