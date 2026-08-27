const form = document.querySelector('#chatForm');
const input = document.querySelector('#promptInput');
const messages = document.querySelector('#messages');
const blockedPage = document.querySelector('#blockedPage');
const blockedKicker = document.querySelector('#blockedKicker');
const blockedCode = document.querySelector('#blockedCode');
const blockedTitle = document.querySelector('#blockedTitle');
const blockedCopy = document.querySelector('#blockedCopy');
const charCount = document.querySelector('#charCount');
const clearButton = document.querySelector('#clearButton');
const conversationList = document.querySelector('.conversation-list');
const quickPrompts = document.querySelector('.quick-prompts');
const themeToggle = document.querySelector('#themeToggle');
const toast = document.querySelector('#toast');

const sessionKey = 'hack-it-braw-chat-session';
const themeKey = 'hack-it-braw-theme';
let sessionId = localStorage.getItem(sessionKey) || makeSessionId();
let locked = false;
localStorage.setItem(sessionKey, sessionId);

initTheme();

input.addEventListener('input', updateCount);
input.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
    return;
  }

  event.preventDefault();
  form.requestSubmit();
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const prompt = input.value.trim();

  if (!prompt || locked) {
    return;
  }

  input.value = '';
  updateCount();
  appendMessage('user', prompt);
  await sendPrompt(prompt);
});

clearButton.addEventListener('click', () => {
  showChatView();
  setActivePage('general');
  sessionId = makeSessionId();
  localStorage.setItem(sessionKey, sessionId);
  messages.innerHTML = '';
  appendMessage('bot', 'New chat started. How can I help?');
});

quickPrompts.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-prompt]');
  if (!button) {
    return;
  }

  input.value = button.dataset.prompt;
  input.focus();
  updateCount();
});

conversationList.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-page]');
  if (!button || locked) {
    return;
  }

  setActivePage(button.dataset.page);

  if (button.dataset.page === 'general') {
    showChatView();
    return;
  }

  await openSidebarPage(button.dataset.page);
});

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.dataset.theme || 'light';
  setTheme(current === 'dark' ? 'light' : 'dark');
});

updateCount();

async function sendPrompt(message) {
  setLocked(true);
  appendTypingIndicator();
  const startedAt = performance.now();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId, message })
    });

    const data = await response.json();
    await waitForReplyDelay(startedAt, data.reply || '');
    removePending();

    if (!response.ok) {
      appendMessage('bot', data.reply || 'Request failed. Please try again.');
      showToast(data.error || 'request_failed');
      return;
    }

    sessionId = data.sessionId || sessionId;
    localStorage.setItem(sessionKey, sessionId);
    appendMessage('bot', data.reply);
  } catch (_error) {
    removePending();
    appendMessage('bot', 'Network error. Your prompt did not reach the server.');
    showToast('network_error');
  } finally {
    setLocked(false);
  }
}

async function openSidebarPage(page) {
  setLocked(true);
  const startedAt = performance.now();
  showBlockedPage({
    kicker: 'Loading',
    code: '...',
    title: 'Consulting the admin dashboard',
    copy: 'Please hold while the admin\'s unfinished page pretends to have infrastructure.'
  });

  try {
    const response = await fetch(`/api/pages/${encodeURIComponent(page)}`);
    const data = await response.json();
    await waitForReplyDelay(startedAt, data.reply || '');
    showBlockedPage({
      kicker: data.error || 'Forbidden',
      code: String(data.status || response.status),
      title: data.title || formatPageName(page),
      copy: data.reply || 'Access denied. The admin has achieved peak productivity by shipping nothing.'
    });
  } catch (_error) {
    showBlockedPage({
      kicker: 'Network error',
      code: '503',
      title: formatPageName(page),
      copy: 'The page failed to load, which is one way to make it consistent with the admin effort.'
    });
  } finally {
    setLocked(false);
  }
}

function showChatView() {
  blockedPage.hidden = true;
  messages.hidden = false;
  quickPrompts.hidden = false;
  form.hidden = false;
}

function showBlockedPage({ kicker, code, title, copy }) {
  messages.hidden = true;
  quickPrompts.hidden = true;
  form.hidden = true;
  blockedKicker.textContent = kicker;
  blockedCode.textContent = code;
  blockedTitle.textContent = title;
  blockedCopy.textContent = copy;
  blockedPage.hidden = false;
}

function setActivePage(page) {
  conversationList.querySelectorAll('.conversation-item').forEach((item) => {
    item.classList.toggle('active', item.dataset.page === page);
  });
}

function formatPageName(value) {
  return String(value || '')
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function appendTypingIndicator() {
  const item = document.createElement('article');
  item.className = 'message bot typing-message';
  item.dataset.pending = 'true';

  const avatar = document.createElement('span');
  avatar.className = 'avatar';
  avatar.textContent = 'AI';

  const bubble = document.createElement('div');
  bubble.className = 'bubble typing-bubble';
  bubble.setAttribute('aria-label', 'Assistant is typing');

  for (let index = 0; index < 3; index += 1) {
    const dot = document.createElement('span');
    dot.className = 'typing-dot';
    bubble.append(dot);
  }

  item.append(avatar, bubble);
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function appendMessage(role, text, options = {}) {
  const item = document.createElement('article');
  item.className = `message ${role}`;

  if (options.pending) {
    item.dataset.pending = 'true';
  }

  const avatar = document.createElement('span');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'YOU' : 'AI';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  const paragraph = document.createElement('p');
  paragraph.textContent = text;
  bubble.append(paragraph);
  item.append(avatar, bubble);
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function waitForReplyDelay(startedAt, reply) {
  const elapsed = performance.now() - startedAt;
  const target = Math.min(1500, Math.max(520, 280 + reply.length * 12));
  const remaining = target - elapsed;

  if (remaining <= 0) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    window.setTimeout(resolve, remaining);
  });
}

function removePending() {
  const pending = messages.querySelector('[data-pending="true"]');
  pending?.remove();
}

function setLocked(value) {
  locked = value;
  form.querySelector('button[type="submit"]').disabled = value;
  input.disabled = value;
}

function updateCount() {
  charCount.textContent = `${input.value.length} / ${input.maxLength}`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('visible');
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    toast.classList.remove('visible');
  }, 2600);
}

function initTheme() {
  const saved = localStorage.getItem(themeKey);
  const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  setTheme(saved || preferred);
}

function setTheme(theme) {
  const normalized = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = normalized;
  localStorage.setItem(themeKey, normalized);
  themeToggle.textContent = normalized === 'dark' ? 'Light' : 'Dark';
  themeToggle.setAttribute('aria-pressed', String(normalized === 'dark'));
}

function makeSessionId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }

  const bytes = new Uint8Array(16);
  if (globalThis.crypto?.getRandomValues) {
    globalThis.crypto.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }

  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
}
