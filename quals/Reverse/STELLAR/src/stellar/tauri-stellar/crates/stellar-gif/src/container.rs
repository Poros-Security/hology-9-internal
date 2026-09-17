use crate::DecodedAnimation;

pub fn encode_sgif(a: &DecodedAnimation) -> Vec<u8> {
    let mut out =
        Vec::with_capacity(24 + a.frames.len() * (24 + a.width as usize * a.height as usize * 4));
    out.extend_from_slice(&0x2ac7_5391u32.to_le_bytes());
    out.extend_from_slice(&1u16.to_le_bytes());
    out.extend_from_slice(&a.width.to_le_bytes());
    out.extend_from_slice(&a.height.to_le_bytes());
    out.extend_from_slice(&(a.frames.len() as u16).to_le_bytes());
    out.extend_from_slice(&a.loop_count.to_le_bytes());
    out.extend_from_slice(&0u32.to_le_bytes());
    for f in &a.frames {
        out.extend_from_slice(&f.delay_cs.to_le_bytes());
        out.push(f.disposal);
        out.push(0);
        out.extend_from_slice(&f.left.to_le_bytes());
        out.extend_from_slice(&f.top.to_le_bytes());
        out.extend_from_slice(&f.width.to_le_bytes());
        out.extend_from_slice(&f.height.to_le_bytes());
        out.extend_from_slice(&(f.rgba.len() as u32).to_le_bytes());
        out.extend_from_slice(&f.rgba);
    }
    out
}
