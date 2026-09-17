use crate::{canvas::Canvas, lzw::decode_lzw, reader::Reader};
use std::{error::Error, fmt};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DecodeError {
    UnexpectedEof,
    InvalidHeader,
    InvalidColorTable,
    InvalidBlock,
    InvalidLzwCode,
    UnexpectedImageData,
    FrameOutOfBounds,
    MissingColorTable,
}
impl fmt::Display for DecodeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::UnexpectedEof => "unexpected end of image data",
            Self::InvalidHeader => "invalid animation header",
            Self::InvalidColorTable => "invalid color table",
            Self::InvalidBlock => "invalid gif block",
            Self::InvalidLzwCode => "invalid lzw code",
            Self::UnexpectedImageData => "unexpected end of image data",
            Self::FrameOutOfBounds => "gif frame outside logical screen",
            Self::MissingColorTable => "gif image has no color table",
        })
    }
}
impl Error for DecodeError {}

#[derive(Debug, Clone)]
pub struct FrameInfo {
    pub index: u32,
    pub left: u16,
    pub top: u16,
    pub width: u16,
    pub height: u16,
    pub delay_cs: u16,
    pub disposal: u8,
    pub transparent_index: Option<u8>,
    pub interlaced: bool,
    pub local_palette: bool,
    pub rgba: Vec<u8>,
    pub after_disposal_rgba: Vec<u8>,
    pub saved_previous_rgba: Option<Vec<u8>>,
    pub lzw_compressed_bytes: usize,
    pub lzw_clear_codes: u16,
    pub lzw_kwkwk_hits: u16,
    pub lzw_max_code_size: u8,
}
#[derive(Debug, Clone)]
pub struct DecodedAnimation {
    pub width: u16,
    pub height: u16,
    pub loop_count: u16,
    pub frames: Vec<FrameInfo>,
    pub application_extensions: u16,
    pub disposal_operations: u16,
}

#[derive(Default, Clone, Copy)]
struct Gce {
    disposal: u8,
    delay: u16,
    transparent: Option<u8>,
}

fn read_palette(r: &mut Reader<'_>, count: usize) -> Result<Vec<[u8; 3]>, DecodeError> {
    if count > 256 {
        return Err(DecodeError::InvalidColorTable);
    }
    Ok(r.take(count * 3)?
        .chunks_exact(3)
        .map(|p| [p[0], p[1], p[2]])
        .collect())
}
fn deinterlace(src: Vec<u8>, w: usize, h: usize) -> Vec<u8> {
    let mut dst = vec![0; src.len()];
    let mut row = 0usize;
    for (start, step) in [(0, 8), (4, 8), (2, 4), (1, 2)] {
        for y in (start..h).step_by(step) {
            dst[y * w..(y + 1) * w].copy_from_slice(&src[row * w..(row + 1) * w]);
            row += 1;
        }
    }
    dst
}
#[inline(never)]
pub fn decode(data: &[u8]) -> Result<DecodedAnimation, DecodeError> {
    let mut r = Reader::new(data);
    let header = r.take(6)?;
    let family = u32::from_le_bytes(header[..4].try_into().unwrap());
    let version = u16::from_le_bytes(header[4..].try_into().unwrap());
    if family != 0x3846_4947 || (version != 0x6137 && version != 0x6139) {
        return Err(DecodeError::InvalidHeader);
    }
    let width = r.u16()?;
    let height = r.u16()?;
    if width == 0 || height == 0 {
        return Err(DecodeError::FrameOutOfBounds);
    }
    let packed = r.u8()?;
    let background_index = r.u8()?;
    let _aspect = r.u8()?;
    let global = if packed & 0x80 != 0 {
        Some(read_palette(&mut r, 1usize << ((packed & 7) + 1))?)
    } else {
        None
    };
    let bg = global
        .as_ref()
        .and_then(|p| p.get(background_index as usize))
        .map(|c| [c[0], c[1], c[2], 255])
        .unwrap_or([0, 0, 0, 0]);
    let mut canvas = Canvas::new(width as usize, height as usize, bg);
    let mut gce = Gce::default();
    let mut frames = Vec::new();
    let mut loop_count = 1u16;
    let mut app_count = 0u16;
    let mut disposal_ops = 0u16;
    loop {
        if r.remaining() == 0 {
            return Err(DecodeError::UnexpectedEof);
        }
        match r.u8()? {
            0x3b => break,
            0x21 => match r.u8()? {
                0xf9 => {
                    if r.u8()? != 4 {
                        return Err(DecodeError::InvalidBlock);
                    }
                    let flags = r.u8()?;
                    let delay = r.u16()?;
                    let trans = r.u8()?;
                    if r.u8()? != 0 {
                        return Err(DecodeError::InvalidBlock);
                    }
                    gce = Gce {
                        disposal: (flags >> 2) & 7,
                        delay,
                        transparent: if flags & 1 != 0 { Some(trans) } else { None },
                    };
                }
                0xff => {
                    let n = r.u8()? as usize;
                    let id = r.take(n)?;
                    let payload = r.sub_blocks()?;
                    if n == 11
                        && (&id[..8] == b"NETSCAPE" || &id[..8] == b"ANIMEXTS")
                        && payload.len() >= 3
                        && payload[0] == 1
                    {
                        loop_count = u16::from_le_bytes([payload[1], payload[2]]);
                    } else {
                        app_count = app_count.wrapping_add(1);
                    }
                }
                0x01 | 0xfe => {
                    let _ = r.sub_blocks()?;
                }
                _ => return Err(DecodeError::InvalidBlock),
            },
            0x2c => {
                let left = r.u16()?;
                let top = r.u16()?;
                let fw = r.u16()?;
                let fh = r.u16()?;
                let flags = r.u8()?;
                let local = flags & 0x80 != 0;
                let interlaced = flags & 0x40 != 0;
                let local_table = if local {
                    Some(read_palette(&mut r, 1usize << ((flags & 7) + 1))?)
                } else {
                    None
                };
                let palette = local_table
                    .as_ref()
                    .or(global.as_ref())
                    .ok_or(DecodeError::MissingColorTable)?;
                let min = r.u8()?;
                let compressed = r.sub_blocks()?;
                let count = fw as usize * fh as usize;
                let (mut indices, lzw_stats) = decode_lzw(min, &compressed, count)?;
                if interlaced {
                    indices = deinterlace(indices, fw as usize, fh as usize);
                }
                let saved = if gce.disposal == 3 {
                    Some(canvas.save(left as usize, top as usize, fw as usize, fh as usize)?)
                } else {
                    None
                };
                canvas.draw(
                    left as usize,
                    top as usize,
                    fw as usize,
                    fh as usize,
                    &indices,
                    palette,
                    gce.transparent,
                )?;
                let rendered = canvas.rgba.clone();
                if gce.disposal == 2 || gce.disposal == 3 {
                    disposal_ops = disposal_ops.wrapping_add(1);
                }
                match gce.disposal {
                    0 | 1 => {}
                    2 => {
                        canvas.background(left as usize, top as usize, fw as usize, fh as usize)?
                    }
                    3 => {
                        canvas.restore_previous(saved.as_ref().ok_or(DecodeError::InvalidBlock)?)?
                    }
                    _ => {}
                }
                frames.push(FrameInfo {
                    index: frames.len() as u32,
                    left,
                    top,
                    width: fw,
                    height: fh,
                    delay_cs: gce.delay,
                    disposal: gce.disposal,
                    transparent_index: gce.transparent,
                    interlaced,
                    local_palette: local,
                    rgba: rendered,
                    after_disposal_rgba: canvas.rgba.clone(),
                    saved_previous_rgba: saved.as_ref().map(|s| s.rgba.clone()),
                    lzw_compressed_bytes: lzw_stats.compressed_bytes,
                    lzw_clear_codes: lzw_stats.clear_codes,
                    lzw_kwkwk_hits: lzw_stats.kwkwk_hits,
                    lzw_max_code_size: lzw_stats.max_code_size,
                });
                gce = Gce::default();
            }
            _ => return Err(DecodeError::InvalidBlock),
        }
    }
    Ok(DecodedAnimation {
        width,
        height,
        loop_count,
        frames,
        application_extensions: app_count,
        disposal_operations: disposal_ops,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_noise() {
        assert_eq!(decode(b"not gif").unwrap_err(), DecodeError::InvalidHeader);
    }
    #[test]
    fn midnight_round_trip() {
        let bytes = include_bytes!("../../../../app/src/assets/gifs/midnight-comet.gif");
        let a = decode(bytes).expect("generated Midnight Comet must decode");
        assert!(a.width > 0 && a.height > 0 && !a.frames.is_empty());
        assert_eq!(a.application_extensions, 0);
        assert!(a.frames.iter().any(|f| f.lzw_max_code_size == 12));
        assert!(a.frames.iter().any(|f| f.lzw_clear_codes > 1));
        assert!(a.frames.iter().any(|f| f.lzw_kwkwk_hits > 0));
    }
}
