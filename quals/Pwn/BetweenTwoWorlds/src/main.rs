
use std::io::{self, Read, Write};
use std::mem::MaybeUninit;

#[repr(C)]
struct Card {
    msg: [u8; 64],
    view_count: u64,

    formatter: Option<extern "C" fn(*mut Card)>,
}

extern "C" {
    fn init_card(card: *mut Card);

    fn load_card(card: *mut Card, src: *const u8, len: usize);


    fn render_card(card: *mut Card);
}

fn main() {

    const MAX_NOTE: usize = 256;

    banner();

    let mut note = Vec::with_capacity(MAX_NOTE);
    io::stdin()
        .take(MAX_NOTE as u64)
        .read_to_end(&mut note)
        .expect("failed to read note");

    let len = note.len().min(MAX_NOTE);

    let mut card = MaybeUninit::<Card>::uninit();


    unsafe {
        init_card(card.as_mut_ptr());
        let card = &mut *card.as_mut_ptr();


        load_card(card, note.as_ptr(), len);

        render_card(card);
    }

    let _ = io::stdout().flush();
}

fn banner() {
    print!(
        "\
==================== SafeNotes v1.0 ====================
 Memory-safe notes, powered by Rust. Native rendering by
 libnotes (C). Paste your note and press Ctrl-D.
========================================================
"
    );
    let _ = io::stdout().flush();
}
