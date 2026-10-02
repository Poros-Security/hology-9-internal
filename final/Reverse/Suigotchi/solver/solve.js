#!/usr/bin/env node
// Author reference: start with `npm run debug`, then run `node solve/solve.js`.
// This talks to Electron's local V8 inspector and invokes the native-backed runtime.

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const port = Number(process.env.SUIGOTCHI_INSPECT_PORT || 9229);
const inspector = `http://127.0.0.1:${port}`;

async function findTarget() {
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch(`${inspector}/json/list`);
      const targets = await response.json();
      const target = targets.find((entry) => entry.webSocketDebuggerUrl);
      if (target) return target;
    } catch (_) {}
    await pause(250);
  }
  throw new Error(`No Electron inspector found on 127.0.0.1:${port}. Start the game with --inspect=${port} first.`);
}

async function main() {
  const target = await findTarget();
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });

  let nextId = 0;
  const pending = new Map();
  socket.addEventListener('message', ({ data }) => {
    const packet = JSON.parse(data);
    const callback = pending.get(packet.id);
    if (callback) {
      pending.delete(packet.id);
      callback(packet);
    }
  });
  const send = (method, params = {}) => new Promise((resolve) => {
    const id = ++nextId;
    pending.set(id, resolve);
    socket.send(JSON.stringify({ id, method, params }));
  });

  await send('Runtime.enable');
  const expression = `(() => {
    const runtime = globalThis[String.fromCharCode(95, 95, 114, 116, 95, 49, 55)];
    runtime.reset();
    const sequence = [6, 1, 3, 7, 2, 5, 3, 6];
    const trace = [];
    for (const action of sequence) {
      const result = runtime.act(action, 0);
      const raw = runtime.snapshotRaw();
      trace.push({ action, state: raw.state, signature: raw.signature, message: result.message });
    }
    return JSON.stringify({ trace, reward: runtime.check(0) });
  })()`;
  const result = await send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (result.error || result.result?.exceptionDetails) {
    throw new Error(JSON.stringify(result.error || result.result.exceptionDetails));
  }
  console.log(result.result.result.value);
  socket.close();
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
