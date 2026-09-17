//! STELLAR Native GIF: the sole behavioral addition in the local Tauri fork.

mod canvas;
mod container;
mod lzw;
mod parser;
mod reader;

pub use container::encode_sgif;
pub use parser::{decode, DecodeError, DecodedAnimation, FrameInfo};
