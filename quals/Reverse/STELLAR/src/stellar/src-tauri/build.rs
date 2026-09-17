fn main() {
    // `tauri-build` normally receives this through the upstream crate's
    // `links = "Tauri"` metadata. STELLAR deliberately puts a path facade in
    // that dependency slot, so forward the one build-time value it consumes.
    let is_dev = std::env::var_os("CARGO_FEATURE_CUSTOM_PROTOCOL").is_none();
    std::env::set_var("DEP_TAURI_DEV", is_dev.to_string());
    tauri_build::build()
}
