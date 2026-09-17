use crate::DecodeError;

pub(crate) struct Reader<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Reader<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        Self { data, pos: 0 }
    }
    pub fn remaining(&self) -> usize {
        self.data.len().saturating_sub(self.pos)
    }
    pub fn u8(&mut self) -> Result<u8, DecodeError> {
        let v = *self.data.get(self.pos).ok_or(DecodeError::UnexpectedEof)?;
        self.pos += 1;
        Ok(v)
    }
    pub fn u16(&mut self) -> Result<u16, DecodeError> {
        let lo = self.u8()? as u16;
        Ok(lo | ((self.u8()? as u16) << 8))
    }
    pub fn take(&mut self, n: usize) -> Result<&'a [u8], DecodeError> {
        let end = self.pos.checked_add(n).ok_or(DecodeError::UnexpectedEof)?;
        let out = self
            .data
            .get(self.pos..end)
            .ok_or(DecodeError::UnexpectedEof)?;
        self.pos = end;
        Ok(out)
    }
    pub fn sub_blocks(&mut self) -> Result<Vec<u8>, DecodeError> {
        let mut out = Vec::new();
        loop {
            let n = self.u8()? as usize;
            if n == 0 {
                break;
            }
            out.extend_from_slice(self.take(n)?);
        }
        Ok(out)
    }
}
