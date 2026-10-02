const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');

const nativePath = path.join(__dirname, '..', 'build', 'Release', 'suigotchi.node');
const native = require(nativePath);
const hiddenPath = path.join(app.getPath('userData'), 'care.json');
const ACTIONS = Object.freeze({ feed: 1, shower: 2, play: 3, sleep: 4 });
const START = Object.freeze([50, 50, 50, 0, 0, 0, 0]);

function suspicionScore() {
  let score = 0;
  try {
    const maps = fs.readFileSync('/proc/self/maps', 'utf8').toLowerCase();
    for (const marker of ['frida', 'gum-js-loop', 'gadget']) {
      if (maps.includes(marker)) score++;
    }
  } catch (_) {}
  try {
    const status = fs.readFileSync('/proc/self/status', 'utf8');
    const tracer = Number((status.match(/^TracerPid:\s*(\d+)/m) || [])[1] || 0);
    if (tracer !== 0) score++;
  } catch (_) {}
  for (const candidate of [
    '/data/local/tmp/frida-server',
    '/data/local/tmp/re.frida.server',
    '/sdcard/frida-server',
    '/tmp/frida-server',
  ]) {
    try { if (fs.existsSync(candidate)) score++; } catch (_) {}
  }
  return score;
}

function freshState() {
  const state = [...START];
  const signature = native.c(state);
  return { state, signature };
}

function loadState() {
  try {
    const stored = JSON.parse(fs.readFileSync(hiddenPath, 'utf8'));
    const state = Array.isArray(stored.state) ? stored.state.map(Number) : [];
    if (state.length === 7 && typeof stored.signature === 'string') {
      const expected = native.c(state);
      if (expected === stored.signature) return { state, signature: stored.signature };
    }
  } catch (_) {}
  return freshState();
}

let pet = loadState();

function persist() {
  fs.mkdirSync(path.dirname(hiddenPath), { recursive: true });
  fs.writeFileSync(hiddenPath, JSON.stringify(pet), { mode: 0o600 });
}

function viewState() {
  const [hunger, bath, fun] = pet.state;
  return {
    hunger: Math.min(hunger, 100),
    bath: Math.min(bath, 100),
    fun: Math.min(fun, 100),
    tick: pet.state[4],
  };
}

function performCare(action, suspicion = suspicionScore()) {
  if (!Number.isInteger(action) || action < 1 || action > 7) {
    return { message: 'Suisei forgot the path of stars.', stats: viewState() };
  }
  const result = native.a(pet.state, action, pet.signature, suspicion);
  pet.signature = result[0];
  persist();
  return { message: result[2], stats: viewState() };
}

function inspectSky(suspicion = suspicionScore()) {
  return native.b(pet.state, pet.signature, suspicion);
}

function resetPet() {
  pet = freshState();
  persist();
  return { message: 'A fresh little star is ready for care.', stats: viewState() };
}

const runtime = Object.freeze({
  act: performCare,
  check: inspectSky,
  reset: resetPet,
  snapshot: viewState,
  snapshotRaw: () => ({ state: [...pet.state], signature: pet.signature }),
  sign: (state) => native.c(state),
});

// The main-process runtime is available to a local V8 inspector session for challenge analysis.
module.exports.__runtime = runtime;
globalThis[String.fromCharCode(95, 95, 114, 116, 95, 49, 55)] = runtime;

ipcMain.handle('pet:snapshot', () => viewState());
ipcMain.handle('pet:care', (_event, actionName) => {
  const action = ACTIONS[actionName];
  if (!action) return { message: 'Suisei forgot the path of stars.', stats: viewState() };
  return performCare(action);
});
ipcMain.handle('pet:check', () => inspectSky());
ipcMain.handle('pet:reset', () => resetPet());

function createWindow() {
  const window = new BrowserWindow({
    width: 1000,
    height: 800,
    minWidth: 320,
    minHeight: 640,
    backgroundColor: '#b7dce4',
    autoHideMenuBar: true,
    title: 'Suigotchi',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  window.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(() => {
  persist();
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
