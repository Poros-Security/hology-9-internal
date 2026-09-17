use crate::DecodeError;

pub(crate) struct Canvas {
    pub width: usize,
    pub height: usize,
    pub rgba: Vec<u8>,
    bg: [u8; 4],
}
pub(crate) struct SavedRegion {
    pub left: usize,
    pub top: usize,
    pub width: usize,
    pub height: usize,
    pub rgba: Vec<u8>,
}

impl Canvas {
    pub fn new(width: usize, height: usize, bg: [u8; 4]) -> Self {
        let mut rgba = vec![0; width * height * 4];
        for p in rgba.chunks_exact_mut(4) {
            p.copy_from_slice(&bg);
        }
        Self {
            width,
            height,
            rgba,
            bg,
        }
    }
    #[inline(never)]
    pub fn save(
        &self,
        left: usize,
        top: usize,
        width: usize,
        height: usize,
    ) -> Result<SavedRegion, DecodeError> {
        self.bounds(left, top, width, height)?;
        let mut rgba = Vec::with_capacity(width * height * 4);
        for y in 0..height {
            let p = ((top + y) * self.width + left) * 4;
            rgba.extend_from_slice(&self.rgba[p..p + width * 4]);
        }
        Ok(SavedRegion {
            left,
            top,
            width,
            height,
            rgba,
        })
    }
    #[inline(never)]
    pub fn draw(
        &mut self,
        left: usize,
        top: usize,
        width: usize,
        height: usize,
        indices: &[u8],
        palette: &[[u8; 3]],
        transparent: Option<u8>,
    ) -> Result<(), DecodeError> {
        self.bounds(left, top, width, height)?;
        for y in 0..height {
            for x in 0..width {
                let idx = indices[y * width + x];
                if Some(idx) == transparent {
                    continue;
                }
                let rgb = palette
                    .get(idx as usize)
                    .ok_or(DecodeError::InvalidColorTable)?;
                let p = ((top + y) * self.width + left + x) * 4;
                self.rgba[p..p + 4].copy_from_slice(&[rgb[0], rgb[1], rgb[2], 255]);
            }
        }
        Ok(())
    }
    #[inline(never)]
    pub fn background(
        &mut self,
        left: usize,
        top: usize,
        width: usize,
        height: usize,
    ) -> Result<(), DecodeError> {
        self.bounds(left, top, width, height)?;
        for y in top..top + height {
            for x in left..left + width {
                let p = (y * self.width + x) * 4;
                self.rgba[p..p + 4].copy_from_slice(&self.bg);
            }
        }
        Ok(())
    }
    #[inline(never)]
    pub fn restore_previous(&mut self, saved: &SavedRegion) -> Result<(), DecodeError> {
        self.bounds(saved.left, saved.top, saved.width, saved.height)?;
        for y in 0..saved.height {
            let dst = ((saved.top + y) * self.width + saved.left) * 4;
            let src = y * saved.width * 4;
            self.rgba[dst..dst + saved.width * 4]
                .copy_from_slice(&saved.rgba[src..src + saved.width * 4]);
        }
        Ok(())
    }
    fn bounds(&self, l: usize, t: usize, w: usize, h: usize) -> Result<(), DecodeError> {
        if l.checked_add(w).is_none()
            || t.checked_add(h).is_none()
            || l + w > self.width
            || t + h > self.height
        {
            Err(DecodeError::FrameOutOfBounds)
        } else {
            Ok(())
        }
    }
}
