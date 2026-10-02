const $ = (id) => document.getElementById(id);

const actionFeedback = {
  feed: { message: 'Suisei munches happily.', mood: 'Snack time is her favorite.' },
  shower: { message: 'Suisei is sparkling clean.', mood: 'Fresh as a little moonbeam.' },
  play: { message: 'Suisei plays with a tiny comet.', mood: 'She found something shiny.' },
  sleep: { message: 'Suisei curls up for a comet nap.', mood: 'Resting under the stars.' },
};

let busy = false;
let effectTimer;

function showMessage(message, mood) {
  $('sky-message').textContent = message;
  $('mood-line').textContent = mood;
}

function update(stats) {
  for (const key of ['hunger', 'bath', 'fun']) {
    const value = Math.max(0, Math.min(100, Number(stats[key]) || 0));
    $(`${key}-number`).textContent = String(value);
    $(`${key}-meter`).style.width = `${value}%`;
    $(`${key}-meter`).parentElement.setAttribute('aria-valuenow', String(value));
  }
  $('cycle-number').textContent = String(stats.tick || 0).padStart(2, '0');
}

function animateAction(action) {
  const room = $('playroom');
  clearTimeout(effectTimer);
  room.classList.remove('is-moving');
  room.dataset.action = action;
  void room.offsetWidth;
  room.classList.add('is-moving');
  effectTimer = setTimeout(() => room.classList.remove('is-moving'), action === 'sleep' ? 1900 : 1350);
}

async function refresh() {
  update(await window.suigotchi.snapshot());
}

document.querySelectorAll('[data-action]').forEach((button) => {
  button.addEventListener('click', async () => {
    if (busy) return;
    busy = true;
    document.querySelectorAll('.care-button').forEach((item) => { item.disabled = true; });
    const action = button.dataset.action;
    try {
      const response = await window.suigotchi.care(action);
      update(response.stats);
      const feedback = actionFeedback[action];
      showMessage(feedback.message, feedback.mood);
      $('sky-message').classList.remove('reward');
      $('playroom').classList.remove('wish-made');
      animateAction(action);
    } catch (_) {
      showMessage('The little star lost her place. Try once more.', 'Waiting for you.');
    } finally {
      busy = false;
      document.querySelectorAll('.care-button').forEach((item) => { item.disabled = false; });
    }
  });
});

$('check-button').addEventListener('click', async () => {
  if (busy) return;
  busy = true;
  const button = $('check-button');
  button.disabled = true;
  try {
    const response = await window.suigotchi.check();
    const isReward = response.startsWith('HOLOGY9{');
    $('sky-message').textContent = response;
    $('mood-line').textContent = isReward ? 'A wish came true. ✦' : 'Suisei is looking up at the stars.';
    $('sky-message').classList.toggle('reward', isReward);
    $('playroom').classList.toggle('wish-made', isReward);
    animateAction(isReward ? 'wish' : 'look');
  } catch (_) {
    showMessage('The stars are a little blurry. Try again in a moment.', 'Looking at the night sky.');
    animateAction('look');
  } finally {
    busy = false;
    button.disabled = false;
  }
});

$('reset-button').addEventListener('click', async () => {
  if (busy) return;
  busy = true;
  const button = $('reset-button');
  button.disabled = true;
  try {
    const response = await window.suigotchi.reset();
    update(response.stats);
    showMessage(response.message, 'A tiny star is waiting for you.');
    $('sky-message').classList.remove('reward');
    $('playroom').classList.remove('wish-made', 'is-moving');
    delete $('playroom').dataset.action;
  } catch (_) {
    showMessage('Suisei could not start over just yet.', 'Still here with you.');
  } finally {
    busy = false;
    button.disabled = false;
  }
});

refresh();
