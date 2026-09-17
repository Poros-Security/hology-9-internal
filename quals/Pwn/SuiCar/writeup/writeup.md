# SuiCar writeup

`SuiTele.calibrate` verifies `PACKED_DOUBLE_ELEMENTS` before calling the
callback. The callback can store an object into the samples array, changing it
to `PACKED_ELEMENTS`. The native code then reuses the stale
`FixedDoubleArray` cast and writes through it without a second kind check.

`SuiArray.fastMap` exposes the same pattern with an index and optional
floating-point write. Its unchecked index is the convenient way to turn the
confusion into controlled 8-byte reads and writes after the callback changes
the array kind.

1. `SuiArray.pack` creates predictable packed-double arrays. A callback changes
   the array to tagged elements, while the stale native pointer still points
   at the old double backing store.
2. An out-of-bounds raw read gives compressed heap addresses. The solve uses
   that as `addrof` and redirects the `rw` array's elements pointer to create a
   fake object, yielding `fakeobj`.
3. The fake object is used to disclose the Wasm trusted instance data, its
   jump-table address, the `WasmInternalFunction`, and the original
   `ArrayBuffer` backing store.
4. The backing-store field of the `ArrayBuffer` is replaced with the Wasm jump
   table. A fresh `Uint8Array` view is then created because typed-array views
   cache their data pointer. The solve writes x86-64 ORW shellcode into the
   jump-table slot.
5. The internal function's call target is overwritten with that slot. Calling
   the exported Wasm function runs the shellcode, which opens `/flag`, reads it,
   and writes it to stdout.
