pub fn run() {
    tauri::stellar::builder()
        .run(tauri::generate_context!())
        .expect("failed to run STELLAR");
}
