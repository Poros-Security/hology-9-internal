use crate::DecodeError;

#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct LzwStats {
    pub compressed_bytes: usize,
    pub clear_codes: u16,
    pub kwkwk_hits: u16,
    pub max_code_size: u8,
}

struct Bits<'a> {
    data: &'a [u8],
    bit: usize,
}
impl<'a> Bits<'a> {
    fn code(&mut self, width: u8) -> Option<u16> {
        if self.bit + width as usize > self.data.len() * 8 {
            return None;
        }
        let mut v = 0u16;
        for i in 0..width as usize {
            v |= (((self.data[(self.bit + i) >> 3] >> ((self.bit + i) & 7)) & 1) as u16) << i;
        }
        self.bit += width as usize;
        Some(v)
    }
}

/// GIF-flavoured LZW with a fixed 4096-entry dictionary.
#[inline(never)]
pub(crate) fn decode_lzw(
    min_size: u8,
    packed: &[u8],
    expected: usize,
) -> Result<(Vec<u8>, LzwStats), DecodeError> {
    if !(2..=8).contains(&min_size) {
        return Err(DecodeError::InvalidLzwCode);
    }
    let clear = 1u16 << min_size;
    let end = clear + 1;
    let mut prefix = [0u16; 4096];
    let mut suffix = [0u8; 4096];
    let mut stack = [0u8; 4096];
    for i in 0..clear as usize {
        suffix[i] = i as u8;
    }
    let mut bits = Bits {
        data: packed,
        bit: 0,
    };
    let mut width = min_size + 1;
    let mut next = end + 1;
    let mut old: Option<u16> = None;
    let mut first = 0u8;
    let mut out = Vec::with_capacity(expected);
    let mut stats = LzwStats {
        compressed_bytes: packed.len(),
        max_code_size: width,
        ..Default::default()
    };

    while let Some(mut code) = bits.code(width) {
        if code == clear {
            stats.clear_codes = stats.clear_codes.saturating_add(1);
            width = min_size + 1;
            next = end + 1;
            old = None;
            continue;
        }
        if code == end {
            break;
        }
        if code > next || code >= 4096 {
            return Err(DecodeError::InvalidLzwCode);
        }
        let incoming = code;
        let mut top = 0usize;
        if code == next {
            stats.kwkwk_hits = stats.kwkwk_hits.saturating_add(1);
            let prev = old.ok_or(DecodeError::InvalidLzwCode)?;
            stack[top] = first;
            top += 1;
            code = prev;
        }
        while code >= clear {
            if top >= stack.len() || code as usize >= 4096 {
                return Err(DecodeError::InvalidLzwCode);
            }
            stack[top] = suffix[code as usize];
            top += 1;
            code = prefix[code as usize];
        }
        first = suffix[code as usize];
        stack[top] = first;
        top += 1;
        while top != 0 {
            top -= 1;
            out.push(stack[top]);
            if out.len() > expected {
                return Err(DecodeError::InvalidLzwCode);
            }
        }
        if let Some(prev) = old {
            if next < 4096 {
                prefix[next as usize] = prev;
                suffix[next as usize] = first;
                next += 1;
                // GIF grows the reader width as soon as the next free code reaches the limit.
                if next == (1u16 << width) && width < 12 {
                    width += 1;
                    stats.max_code_size = stats.max_code_size.max(width);
                }
            }
        }
        old = Some(incoming);
    }
    if out.len() != expected {
        return Err(DecodeError::UnexpectedImageData);
    }
    Ok((out, stats))
}
