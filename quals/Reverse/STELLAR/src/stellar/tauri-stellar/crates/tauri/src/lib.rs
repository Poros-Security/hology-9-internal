//! A deliberately narrow fork of Tauri 2.8.5.
//! The only behavioral change is `stellar::builder`, which adds native GIF assets.
pub use tauri_upstream::*;

pub mod stellar;
