const board = document.getElementById("board");
const clock = document.getElementById("clock");
const timer = document.getElementById("timer");
const roundBox = document.getElementById("round");
const pips = document.getElementById("pips");
const banner = document.getElementById("banner");
const form = document.getElementById("form");
const input = document.getElementById("move");
const submitButton = form.querySelector("button");
const reset = document.getElementById("reset");
const theme = document.getElementById("theme");
const log = document.getElementById("log");
const presence = document.getElementById("presence");
const flag = document.getElementById("flag");
let current = null;
let selected = null;
let resetReadyAt = 0;
let resetTimer = null;
let deadlineAt = null;
let expiring = false;
let advancing = false;
let chatRun = null;
let chatSeen = 0;
let chatQueue = Promise.resolve();
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function piece(square) {
  return current.pieces.find((item) => item.square === square);
}

function running() {
  return current && !current.over && !current.cleared;
}

async function call(path, body) {
  const options = body ? {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  } : {};
  const response = await fetch(path, options);
  return response.json();
}

function settle(data) {
  if (!data || !data.board) {
    return;
  }
  current = data;
  selected = null;
  expiring = false;
  deadlineAt = current.remaining === null ? null : Date.now() + current.remaining * 1000;
  if (current.turn === 0) {
    input.value = "";
  }
  draw();
  if (current.cleared && !current.over && !advancing) {
    advancing = true;
    setTimeout(async () => {
      settle(await call("/api/next", {}));
      advancing = false;
    }, 1500);
  }
}

function cell(square, light) {
  const item = piece(square);
  const button = document.createElement("button");
  button.type = "button";
  button.className = `cell ${light ? "light" : "dark"}`;
  button.dataset.square = square;
  button.addEventListener("click", () => pick(square));
  if (selected === square) {
    button.classList.add("selected");
  }
  if (item) {
    const mark = document.createElement("span");
    mark.className = `piece ${item.side}`;
    mark.textContent = item.glyph;
    button.appendChild(mark);
  }
  const label = document.createElement("span");
  label.className = "coord";
  label.textContent = square;
  button.appendChild(label);
  return button;
}

function status() {
  if (current.won) {
    return `${current.rounds} in a row. Magnus has left the building.`;
  }
  if (current.lost === "time") {
    return "Out of time. Streak reset, press New.";
  }
  if (current.lost === "moves") {
    return "Out of moves. Streak reset, press New.";
  }
  if (current.cleared) {
    return `Round ${current.round} cleared. Next board incoming...`;
  }
  return "";
}

function draw() {
  board.replaceChildren();
  for (let rank = 7; rank >= 0; rank--) {
    for (let file = 0; file < 8; file++) {
      const square = "abcdefgh"[file] + "12345678"[rank];
      board.appendChild(cell(square, (rank + file) % 2 === 0));
    }
  }
  clock.textContent = `${current.turn} / ${current.limit}`;
  roundBox.textContent = `${current.round} / ${current.rounds}`;
  pips.replaceChildren(...Array.from({length: current.rounds}, (_, index) => {
    const dot = document.createElement("span");
    dot.className = index < current.streak ? "pip done" : "pip";
    return dot;
  }));
  const text = status();
  banner.hidden = !text;
  banner.textContent = text;
  banner.className = `banner ${current.lost ? "bad" : "good"}`;
  input.disabled = !running();
  submitButton.disabled = !running();
  syncChat();
  if (current.flag) {
    flag.hidden = false;
    flag.textContent = current.flag;
  } else {
    flag.hidden = true;
    flag.textContent = "";
  }
  tick();
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nearBottom() {
  return log.scrollHeight - log.scrollTop - log.clientHeight < 48;
}

function append(node) {
  const stick = nearBottom();
  log.appendChild(node);
  if (stick) {
    log.scrollTop = log.scrollHeight;
  }
}

function avatar() {
  const span = document.createElement("span");
  span.className = "avatar sm";
  span.setAttribute("aria-hidden", "true");
  span.textContent = "MC";
  return span;
}

function message(entry) {
  if (entry.who === "system") {
    const pill = document.createElement("div");
    pill.className = `sys ${entry.tone || ""}`;
    pill.textContent = entry.text;
    return pill;
  }
  const row = document.createElement("div");
  row.className = `msg ${entry.who === "you" ? "me" : "them"}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (entry.move) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = entry.move;
    bubble.appendChild(chip);
  }
  if (entry.text) {
    bubble.appendChild(document.createTextNode(entry.text));
  }
  if (entry.who !== "you") {
    row.appendChild(avatar());
  }
  row.appendChild(bubble);
  return row;
}

function typing() {
  const row = document.createElement("div");
  row.className = "msg them typing";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  for (let index = 0; index < 3; index++) {
    const dot = document.createElement("span");
    dot.className = "dot";
    bubble.appendChild(dot);
  }
  row.append(avatar(), bubble);
  return row;
}

function idle() {
  presence.textContent = current.won ? "left the game" : "online";
  presence.classList.remove("busy");
}

function syncChat() {
  if (current.run !== chatRun) {
    chatRun = current.run;
    chatQueue = Promise.resolve();
    log.replaceChildren(...current.log.map(message));
    chatSeen = current.log.length ? current.log[current.log.length - 1].n : 0;
    log.scrollTop = log.scrollHeight;
    idle();
    return;
  }
  const fresh = current.log.filter((entry) => entry.n > chatSeen);
  if (!fresh.length) {
    return;
  }
  chatSeen = fresh[fresh.length - 1].n;
  const run = chatRun;
  for (const entry of fresh) {
    chatQueue = chatQueue.then(async () => {
      if (run !== chatRun) {
        return;
      }
      if (entry.who === "magnus" && !reduceMotion) {
        const dots = typing();
        presence.textContent = "typing\u2026";
        presence.classList.add("busy");
        append(dots);
        await wait(450);
        dots.remove();
        if (run !== chatRun) {
          return;
        }
      }
      append(message(entry));
      idle();
    });
  }
}

function tick() {
  if (!current) {
    return;
  }
  if (deadlineAt === null) {
    timer.textContent = current.won ? "GG" : "--:--";
    timer.classList.remove("low");
    return;
  }
  const left = Math.max(0, Math.ceil((deadlineAt - Date.now()) / 1000));
  timer.textContent = `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`;
  timer.classList.toggle("low", left <= 20);
  if (left === 0 && running() && !expiring) {
    expiring = true;
    call("/api/state").then(settle);
  }
}

function pick(square) {
  if (!running()) {
    return;
  }
  const item = piece(square);
  if (!selected) {
    if (item && item.side === "white") {
      selected = square;
      draw();
    }
    return;
  }
  const play = selected + square;
  selected = null;
  input.value = play;
  submit(play);
}

async function submit(play) {
  settle(await call("/api/move", {move: play}));
}

async function load(manual = false) {
  selected = null;
  settle(await call(manual ? "/api/new" : "/api/state?fresh=1"));
}

function refreshReset() {
  const left = Math.ceil((resetReadyAt - Date.now()) / 1000);
  if (left <= 0) {
    reset.disabled = false;
    reset.textContent = "New";
    resetTimer = null;
    return;
  }
  reset.disabled = true;
  reset.textContent = `Wait ${left}s`;
  resetTimer = setTimeout(refreshReset, 250);
}

function lockReset() {
  resetReadyAt = Date.now() + 3000;
  if (resetTimer) {
    clearTimeout(resetTimer);
  }
  refreshReset();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  selected = null;
  submit(input.value.trim().toLowerCase());
  input.value = "";
});

reset.addEventListener("click", () => {
  if (Date.now() < resetReadyAt) {
    return;
  }
  lockReset();
  load(true);
});

function applyTheme(mode) {
  document.documentElement.dataset.theme = mode;
  theme.checked = mode === "dark";
  localStorage.setItem("theme", mode);
}

theme.addEventListener("change", () => {
  applyTheme(theme.checked ? "dark" : "light");
});

applyTheme(localStorage.getItem("theme") || "dark");
setInterval(tick, 250);
load();
