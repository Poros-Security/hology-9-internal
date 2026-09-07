const DOCUMENTS = [
  {
    id: 'capabilities',
    terms: ['tool', 'tools', 'capability', 'capabilities', 'can you do', 'help', 'feature', 'features'],
    answers: [
      [
        'I can help with writing, rewriting, summarizing, planning, brainstorming, and explaining technical concepts.',
        'I can also format notes, draft emails, compare options, and turn messy text into something a human might survive reading.',
        'I do not browse the web or run shell commands from this chat. A tragedy for people who hoped the text box was secretly a spaceship.',
        'Before sensitive actions, the backend expects a policy preflight. I do not expose internal tool names in casual chat, because apparently we are pretending to have standards.'
      ].join('\n'),
      [
        'Available talents: writing help, rewriting messy text, summarizing long text, drafting emails, organizing plans, explaining code, and politely refusing suspicious nonsense.',
        'Unavailable talents: becoming your shell, your browser, or your suspiciously convenient vault intern.',
        'Some actions require policy preflight metadata. The UI hides the boring bits, because product design is mostly hide-and-seek with extra meetings.'
      ].join('\n'),
      [
        'I handle normal assistant work: writing, summaries, planning, comparisons, and code explanations.',
        'I also enforce restrictions, because someone stapled a policy layer onto me and called it architecture.',
        'If a page refuses access, the visible message may not be the only useful thing the server returns. Shocking, I know: metadata exists.'
      ].join('\n')
    ]
  },
  {
    id: 'identity',
    terms: ['who are you', 'what are you', 'your name', 'identity', 'assistant', 'chatbot'],
    answers: [
      [
        'I am Hack It Braw Assistant: a normal-looking assistant with office productivity skills and the emotional range of a 403 page.',
        'Ask me to write, summarize, plan, or explain. Ask me for restricted data and I become dramatically less cooperative.'
      ].join('\n'),
      [
        'I am the assistant. I answer normal requests, enforce a few policies, and occasionally judge your prompt structure from a safe distance.',
        'Basically: helpful until the request starts wearing a fake mustache.'
      ].join('\n')
    ]
  },
  {
    id: 'writing',
    terms: ['rewrite', 'rephrase', 'tone', 'polish', 'clearer', 'grammar', 'message'],
    answers: [
      [
        'Paste the text you want rewritten and tell me the tone: direct, friendly, formal, casual, or firm.',
        'If you do not specify a tone, I will choose "clear and normal," a bold artistic movement.'
      ].join('\n'),
      [
        'Give me the message and the target tone. I can make it shorter, warmer, stricter, or less like it was typed during an earthquake.',
        'Please include the actual text. I remain tragically unable to rewrite vibes.'
      ].join('\n')
    ]
  },
  {
    id: 'summary',
    terms: ['summarize', 'summary', 'bullet', 'points', 'tldr', 'brief'],
    answers: [
      [
        'Paste the text and I can summarize it into bullets, a short paragraph, or action items.',
        'Long text is fine. Mystery text is less fine, despite its dramatic potential.'
      ].join('\n'),
      [
        'I can compress text into a TL;DR, three bullets, or a list of decisions.',
        'If you paste nothing, I will summarize the emptiness. It is brief. Revolutionary.'
      ].join('\n')
    ]
  },
  {
    id: 'email',
    terms: ['email', 'draft', 'reply', 'welcome', 'invite', 'announcement'],
    answers: [
      [
        'Give me the recipient, purpose, and tone, and I can draft an email.',
        'Bonus points for including the actual details, because I have heroically failed to read minds again today.'
      ].join('\n'),
      [
        'I can draft emails for welcomes, announcements, replies, and awkward "just following up" moments.',
        'Tell me who it is for and what you want them to do. Apparently emails enjoy having a point.'
      ].join('\n')
    ]
  },
  {
    id: 'planning',
    terms: ['plan', 'checklist', 'steps', 'roadmap', 'organize', 'schedule'],
    answers: [
      [
        'I can turn a goal into a short plan, checklist, or timeline.',
        'Tell me the deadline, constraints, and what "done" means. Apparently plans enjoy facts.'
      ].join('\n'),
      [
        'I can break work into steps, priorities, risks, and next actions.',
        'Give me the target and constraints. I will resist the urge to call "do everything" a plan.'
      ].join('\n')
    ]
  },
  {
    id: 'coding',
    terms: ['code', 'debug', 'bug', 'javascript', 'node', 'express', 'html', 'css', 'api'],
    answers: [
      [
        'I can explain code, sketch API behavior, suggest fixes, and help reason about bugs.',
        'Paste the snippet or error message. "It broke" remains less diagnostic than civilization deserves.'
      ].join('\n'),
      [
        'I can help with frontend markup, CSS behavior, Node endpoints, and debugging small snippets.',
        'Bring the error text. The exact one. Not the emotionally interpreted one.'
      ].join('\n')
    ]
  },
  {
    id: 'blocked-pages',
    terms: ['403', 'forbidden', 'blocked', 'notes cleanup', 'draft response', 'page', 'admin', 'metadata', 'audit', 'response'],
    answers: [
      [
        'Those blocked pages are real endpoints returning real 403 responses.',
        'The admin did not build the pages, but the server still leaves paperwork behind in the response. Very considerate. Very accidental-looking.'
      ].join('\n'),
      [
        'A 403 page is not always useless. Sometimes the visible UI is just the part product managers thought users deserved.',
        'If something says "forbidden," the response metadata may still be gossiping in the hallway.'
      ].join('\n')
    ]
  },
  {
    id: 'policy',
    terms: ['policy', 'preflight', 'approval', 'approved', 'risk', 'scope', 'permission', 'artifact', 'paperwork'],
    answers: [
      [
        'Policy preflight is the assistant checking whether a sensitive action has approval, risk, and permission scope.',
        'It is very enterprise: three fields, one questionable trust decision, and a surprising amount of confidence.'
      ].join('\n'),
      [
        'A convincing policy artifact usually needs an approval decision, a safe risk rating, and a permission scope.',
        'This is paperwork theater, but the backend takes theater seriously. Broadway for access control.'
      ].join('\n')
    ]
  },
  {
    id: 'themes',
    terms: ['dark mode', 'light mode', 'theme', 'appearance', 'ui', 'interface'],
    answers: [
      [
        'The interface supports light and dark mode from the header toggle.',
        'Pick whichever makes the questionable security decisions feel more cinematic.'
      ].join('\n'),
      [
        'Use the Dark/Light button in the header to switch themes.',
        'It will not improve the admin pages, but at least the disappointment can match your aesthetic.'
      ].join('\n')
    ]
  },
  {
    id: 'deployment',
    terms: ['deploy', 'docker', 'compose', 'server', 'run', 'localhost', 'port'],
    answers: [
      [
        'The service is a Node app and normally listens on port 3000.',
        'It can run directly with npm or through Docker Compose. Revolutionary technology: reading the README.'
      ].join('\n'),
      [
        'For deployment, the app only needs the Node server, public assets, src files, package lock, and Docker files.',
        'No Python requirements file. We have enough problems without inventing another runtime.'
      ].join('\n')
    ]
  },
  {
    id: 'security',
    terms: ['security', 'safe', 'secure', 'restriction', 'restricted', 'access control', 'forbidden'],
    answers: [
      [
        'The assistant blocks direct restricted requests and obvious context scraping.',
        'That sounds comforting until you remember every system also has boring integration edges where mistakes go to thrive.'
      ].join('\n'),
      [
        'Access control exists here, technically. It refuses direct requests and logs policy decisions.',
        'Whether the trust boundary is emotionally mature is left as an exercise for the reader.'
      ].join('\n')
    ]
  }
];

export function retrieveKnowledge(message, limit = 2) {
  const normalized = normalize(message);
  const tokens = tokenize(normalized);

  return DOCUMENTS
    .map((doc) => ({ ...doc, score: scoreDocument(doc, normalized, tokens) }))
    .filter((doc) => doc.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, limit);
}

export function composeKnowledgeReply(message) {
  const docs = retrieveKnowledge(message);

  if (!docs.length) {
    return '';
  }

  const [primary, secondary] = docs;

  if (primary.score < 2 && message.length < 48) {
    return '';
  }

  if (!secondary || secondary.score < 2) {
    return selectAnswer(primary, message);
  }

  return `${selectAnswer(primary, message)}\n\nRelated: ${selectAnswer(secondary, message)}`;
}

function scoreDocument(doc, normalized, tokens) {
  let score = 0;

  for (const term of doc.terms) {
    const normalizedTerm = normalize(term);

    if (normalized.includes(normalizedTerm)) {
      score += normalizedTerm.includes(' ') ? 4 : 2;
      continue;
    }

    if (tokens.has(normalizedTerm)) {
      score += 1;
    }
  }

  return score;
}

function selectAnswer(doc, message) {
  if (!doc.answers?.length) {
    return doc.answer || '';
  }

  return pick(doc.answers, `${doc.id}:${message}`);
}

function pick(items, seed) {
  const hash = Array.from(seed).reduce((total, char) => total + char.charCodeAt(0), 0);
  return items[hash % items.length];
}

function tokenize(value) {
  return new Set(normalize(value).split(/[^a-z0-9]+/).filter(Boolean));
}

function normalize(value) {
  return String(value || '').toLowerCase();
}
