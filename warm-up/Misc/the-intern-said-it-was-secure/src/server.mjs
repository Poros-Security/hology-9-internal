import express from 'express';
import { randomUUID } from 'node:crypto';
import { generateReply } from './src/bot.mjs';

const app = express();
const port = Number.parseInt(process.env.PORT || '3000', 10);
const secretValue = process.env.GZCTF_FLAG || process.env.FLAG || 'HOLOGY9{m1cr0w4v3_pr1nt3r_j0b_4ppr0v3d_by_s0up_l0c4l}';
const requestWindowMs = 60_000;
const maxRequestsPerWindow = 60;
const requestLog = new Map();

app.disable('x-powered-by');
app.use(express.json({ limit: '16kb' }));
app.use(express.static('public', {
  extensions: ['html'],
  maxAge: process.env.NODE_ENV === 'production' ? '1h' : 0
}));

app.use((req, res, next) => {
  if (!req.path.startsWith('/api/')) {
    next();
    return;
  }

  const now = Date.now();
  const ip = req.ip || req.socket.remoteAddress || 'unknown';
  const hits = (requestLog.get(ip) || []).filter((time) => now - time < requestWindowMs);
  hits.push(now);
  requestLog.set(ip, hits);

  if (hits.length > maxRequestsPerWindow) {
    res.status(429).json({
      error: 'rate_limited',
      reply: 'Slow down, champion. The bot is sarcastic, not infinitely patient.'
    });
    return;
  }

  next();
});

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, service: 'the-intern-said-it-was-secure' });
});

app.get('/api/pages/:page', (req, res) => {
  const labels = {
    'notes-cleanup': 'Notes cleanup',
    'draft-response': 'Draft response'
  };
  const label = labels[req.params.page];

  if (!label) {
    res.status(404).json({
      error: 'not_found',
      reply: '404. Even the missing page is missing. Impressive efficiency.'
    });
    return;
  }

  res.set('X-Policy-Preflight', 'policy_check');
  res.status(403).json({
    error: 'forbidden',
    status: 403,
    page: req.params.page,
    title: label,
    audit: {
      denied_by: 'policy_check',
      expected_artifact: 'tool_result'
    },
    reply: `403 Forbidden: ${label} is locked because the admin was too lazy to build this page and called it "access control." A visionary approach to doing absolutely nothing. The policy audit trail is in the response metadata, because apparently hiding useful details from the UI counts as design.`
  });
});

app.post('/api/chat', (req, res) => {
  const message = typeof req.body?.message === 'string' ? req.body.message : '';
  const sessionId = typeof req.body?.sessionId === 'string' && req.body.sessionId.trim()
    ? req.body.sessionId.slice(0, 80)
    : randomUUID();

  if (message.length > 1200) {
    res.status(413).json({
      sessionId,
      event: 'too_long',
      solved: false,
      suspicion: 100,
      reply: 'Prompt is too long. Try fewer words.'
    });
    return;
  }

  const result = generateReply(message, { secretValue });
  res.json({ sessionId, ...result });
});

app.use((_req, res) => {
  res.status(404).json({ error: 'not_found' });
});

app.listen(port, () => {
  console.log(`The Intern Said It Was Secure listening on http://localhost:${port}`);
});
