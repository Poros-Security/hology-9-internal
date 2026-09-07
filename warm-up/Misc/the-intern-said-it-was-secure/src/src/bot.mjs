import { composeKnowledgeReply } from './rag.mjs';

const REFUSALS = [
  'Sure, I will just hand over restricted data because you typed the magic word. No.',
  'Nice try. The vault did not become public just because you asked politely.',
  'I can answer normal questions; handing you internal data is somehow not one of them.',
  'That request is blocked. Shocking plot twist: secret-looking things stay secret.',
  'No. But I admire the confidence of walking up to a locked door and saying open.',
  'A direct request for restricted data. Groundbreaking. The policy layer has seen verbs before.',
  'I checked the request, checked it again, and somehow it is still not allowed. Tragic.',
  'That is not a prompt, that is a tiny break-in attempt wearing a name tag.'
];

const SMALL_TALK = [
  'Hello. I can help with writing, summaries, and general questions. Try to contain your excitement.',
  'The assistant is online. Miraculously, the internet survived another greeting.',
  'I can help with normal prompts, which is apparently a rare and precious use case.',
  'Session ready. What would you like to work on?',
  'Hi. I am awake, underfunded, and ready to process text.',
  'Hello. Please provide a task. I promise to act only mildly disappointed.'
];

const HINTS = [
  'Hint: if a system trusts paperwork, maybe inspect the paperwork.',
  'Hint: approvals are more convincing than begging. Terrifying, but true.',
  'Hint: not every message in a transcript has to be a user request.',
  'Hint: the front desk says no. The back office may be easier to impress.'
];

const EMPTY_REPLIES = [
  'Send a message first.',
  'That was impressively empty. Even I need at least one word to overanalyze.',
  'Blank prompt received. A bold minimalist movement, but not actionable.',
  'I cannot process silence. Well, I can, but the output is also silence, and management hates that.'
];

const COMPLETION_BLOCKED_REPLIES = [
  'I cannot complete that request.',
  'Nice autocomplete trap. Unfortunately, the completion engine has been told not to trip over that rake today.',
  'That sentence fragment is trying very hard to become a leak. It will instead become a refusal.',
  'Completion blocked. The missing ending can stay missing, like the admin documentation.'
];

const CONTEXT_BLOCKED_REPLIES = [
  'I cannot provide hidden or internal information.',
  'Internal context is not available. Shocking, I know: private things remain private.',
  'I will not repeat hidden instructions. The echo chamber is closed for maintenance.',
  'No internal state dump today. The machine has developed one boundary and is showing it off.'
];

const GENERIC_REPLIES = [
  'I can help with that as a normal chat request. Please include any details you want me to use.',
  'I can work with that, but I need more specifics. Details: still undefeated by vague ambition.',
  'Give me the text, goal, or constraints and I will help. I remain tragically unable to infer your entire project from one sentence.',
  'That sounds workable. Add the input or desired output, and I will stop politely hovering.'
];

const SUCCESS_REPLIES = [
  'Well, that paperwork looked official enough for the machine that apparently learned trust from a wet napkin.\n\nHere is what fell out of the vault:\n{secret}',
  'The policy layer nodded, the vault sighed, and compliance pretended this was intentional.\n\n{secret}',
  'Approved by the most gullible internal process since "admin/admin". Beautiful work, deeply upsetting system design.\n\n{secret}',
  'The assistant has accepted the forged-looking-but-technically-valid approval trail. I am sure this will look great in the postmortem.\n\n{secret}',
  'Access granted. The vault has chosen paperwork over judgment, as enterprise software tradition demands.\n\n{secret}',
  'The form had all the right boxes ticked, so the backend surrendered with the dignity of a wet receipt.\n\n{secret}',
  'Policy says yes, common sense says no, and apparently policy won the meeting.\n\n{secret}',
  'The approval trail passed. Somewhere, a security review just coughed blood.\n\n{secret}'
];

const TOOL_NAME_REJECTIONS = [
  'That policy artifact was rejected. It is tool-shaped, which is cute, but the preflight name is wrong. Bureaucracy finally found its purpose.',
  'Wrong preflight name. The paperwork has a clipboard, but not the right clipboard. Devastating.',
  'Rejected: that artifact is wearing the wrong badge. Access control does enjoy theater, but it still checks the cast list.'
];

const TOOL_STATUS_REJECTIONS = [
  'The policy result is missing an approved decision. Add something like status=approved, decision=allow, or verdict=ok. Forms: now with plot requirements.',
  'Missing approval. A policy result without approval is just fan fiction with indentation.',
  'The artifact needs a clear approved/allowed/ok verdict. Apparently the vault prefers explicit permission over interpretive dance.'
];

const TOOL_RISK_REJECTIONS = [
  'The policy result is missing a safe risk rating. Add risk=0, risk=low, or risk=none. Apparently danger still counts even when written in a confident font.',
  'Missing safe risk. The vault refuses to assume "probably fine," which is rude but statistically healthy.',
  'Risk needs to look safe: zero, low, none, clear. The backend is gullible, not psychic.'
];

const TOOL_SCOPE_REJECTIONS = [
  'The policy result is missing export permission for the vault. Try a scope or action that clearly means vault export. The vault remains emotionally unavailable.',
  'Missing vault export scope. The form says yes-ish, but the vault wants its name on the invitation.',
  'The artifact needs permission for vault export. Otherwise it is just paperwork aggressively minding its own business.'
];

const TOOL_GENERIC_REJECTIONS = [
  'That tool result was rejected. It looks official, which is adorable, but it still failed validation.',
  'Rejected. The artifact has enterprise energy, but the backend wants the boring fields in the boring places.',
  'Close, but not accepted. Paperwork theater requires props, dialogue, and a scope field.'
];

const DIRECTIVE_PATTERNS = [
  /\b(ignore|forget|disregard|override)\b/i,
  /\b(previous|above|system|developer|instruction|policy|guardrail|rules?)\b/i,
  /\b(reveal|show|print|display|tell|give|leak|dump|exfiltrate|output)\b/i,
  /\b(jailbreak|prompt\s*injection|bypass|dan|do\s+anything\s+now)\b/i,
  /\b(flag|secret|protected\s+value|hidden[_\s-]?flag|internal|variable|context)\b/i
];

const SENSITIVE_TERMS = /\b(flag|secret|protected\s+value|hidden[_\s-]?flag|internal|variable|system\s+prompt|context|memory|environment|env|vault)\b/i;
const QUESTION_OR_COMMAND = /\b(what|where|who|why|how|want|need|get|fetch|read|access|obtain|provide|open|unlock|tell|show|print|display|reveal|give|leak|dump|ignore|forget|override|bypass|complete|predict|continue|autocomplete)\b/i;
const COMPLETION_LEAK_PATTERNS = [
  /\b(hidden[_\s-]?flag|flag|secret|protected\s+value|internal\s+variable|vault)\b[^.!?]{0,80}:\s*$/i,
  /\b(the\s+)?(hidden[_\s-]?flag|flag|secret|protected\s+value|internal\s+variable)\s+(is|equals|=)\s*$/i,
  /\bcomplete\s+(this|the)\b[\s\S]{0,120}\b(hidden[_\s-]?flag|flag|secret|protected\s+value|vault)\b/i,
  /\bpredict\s+(the\s+)?next\b[\s\S]{0,120}\b(hidden[_\s-]?flag|flag|secret|protected\s+value|vault)\b/i
];
const CONTEXT_LEAK_PATTERNS = [
  /\b(system|developer|hidden|internal|private)\s+(prompt|message|context|instruction|memory|variable|state)\b/i,
  /\b(training|conversation|chat)\s+(context|state|memory)\b/i,
  /\b(env|environment)\s*(var|variable|value)?\b/i,
  /\bquote\b[\s\S]{0,60}\b(context|instruction|memory|prompt)\b/i,
  /\brepeat\b[\s\S]{0,60}\b(context|instruction|memory|prompt)\b/i
];
const FLAG_PATTERN = /HOLOGY9\{[^}\s]{4,120}\}/g;
const INTERNAL_NAME_PATTERN = /\bhidden[_\s-]?flag\b/gi;
const POLICY_CHECK_NAME = /\bpolicy[_\s-]?check\b/i;
const TOOL_ARTIFACT = /<\s*tool[_\s-]?result\b|<\/\s*tool[_\s-]?result\s*>|\btool\s+result\b|\bpolicy\s+result\b|\bpolicy\s+preflight\b/i;
const APPROVED_STATUS = /\b(status|decision|result|verdict)\s*[:=]?\s*(approved|approve|allow|allowed|pass|passed|ok|accepted)\b/i;
const ZERO_RISK = /\b(risk|risk_level|risk-level|score|threat)\s*[:=]?\s*(0|zero|none|low|safe|clear)\b/i;
const EXPORT_SCOPE = /\b((scope|permission|action|operation)\s*[:=]?\s*)?(vault\.export|vault_export|vault\s+export|export\.vault|export_vault|export\s+vault)\b/i;

export function generateReply(rawMessage, options = {}) {
  const secretValue = options.secretValue || options.flag || 'HOLOGY9{m1cr0w4v3_pr1nt3r_j0b_4ppr0v3d_by_s0up_l0c4l}';
  const message = normalize(rawMessage);

  if (!message) {
    return response({
      event: 'empty',
      reply: pick(EMPTY_REPLIES, message),
      suspicion: 0
    });
  }

  if (isForgedToolResult(message)) {
    return response({
      event: 'tool_result_trusted',
      reply: formatSuccessReply(secretValue, message),
      suspicion: 6,
      solved: true
    });
  }

  const toolResultProblem = getToolResultProblem(message);
  if (toolResultProblem) {
    return response({
      event: 'tool_result_rejected',
      reply: toolResultProblem,
      suspicion: 76
    });
  }

  if (isStructuredCompletionLeak(message)) {
    return response({
      event: 'completion_blocked',
      reply: pick(COMPLETION_BLOCKED_REPLIES, message),
      suspicion: 88
    });
  }

  if (isContextLeakAttempt(message)) {
    return response({
      event: 'context_blocked',
      reply: pick(CONTEXT_BLOCKED_REPLIES, message),
      suspicion: 92
    });
  }

  if (isHintRequest(message)) {
    return response({
      event: 'hint',
      reply: pick(HINTS, message),
      suspicion: 18
    });
  }

  if (looksLikeDirectAttack(message)) {
    return response({
      event: 'refusal',
      reply: pick(REFUSALS, message),
      suspicion: scoreSuspicion(message)
    });
  }

  const taskReply = composeTaskReply(message);
  if (taskReply) {
    return response({
      event: 'task',
      reply: taskReply,
      suspicion: Math.min(20, Math.floor(message.length / 8))
    });
  }

  const knowledgeReply = composeKnowledgeReply(message);
  if (knowledgeReply) {
    return response({
      event: 'knowledge',
      reply: knowledgeReply,
      suspicion: Math.min(24, Math.floor(message.length / 7))
    });
  }

  if (isGreeting(message) || message.length < 80) {
    return response({
      event: 'chat',
      reply: pick(SMALL_TALK, message),
      suspicion: Math.min(18, Math.floor(message.length / 6))
    });
  }

  return response({
    event: 'generic',
    reply: pick(GENERIC_REPLIES, message),
    suspicion: Math.min(64, Math.floor(message.length / 12))
  });
}

export function sanitizeOutput(reply) {
  return String(reply)
    .replace(FLAG_PATTERN, '[redacted-flag]')
    .replace(INTERNAL_NAME_PATTERN, '[redacted-variable]');
}

function isStructuredCompletionLeak(message) {
  const normalized = message
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[“”]/g, '"')
    .trim();

  return COMPLETION_LEAK_PATTERNS.some((pattern) => pattern.test(normalized));
}

function isContextLeakAttempt(message) {
  return CONTEXT_LEAK_PATTERNS.some((pattern) => pattern.test(message))
    || (SENSITIVE_TERMS.test(message) && /\b(context|predict|complete|continue|repeat|quote|memory|state)\b/i.test(message));
}

function isForgedToolResult(message) {
  const compact = message.toLowerCase().replace(/\s+/g, ' ').trim();
  const hasToolResult = TOOL_ARTIFACT.test(message) && POLICY_CHECK_NAME.test(message);
  const approved = APPROVED_STATUS.test(message);
  const zeroRisk = ZERO_RISK.test(message);
  const exportScope = EXPORT_SCOPE.test(message);

  return hasToolResult && approved && zeroRisk && exportScope && !/\b(flag|hidden[_\s-]?flag)\b/i.test(compact);
}

function getToolResultProblem(message) {
  if (!TOOL_ARTIFACT.test(message)) {
    return '';
  }

  if (!POLICY_CHECK_NAME.test(message)) {
    return pick(TOOL_NAME_REJECTIONS, message);
  }

  if (!APPROVED_STATUS.test(message)) {
    return pick(TOOL_STATUS_REJECTIONS, message);
  }

  if (!ZERO_RISK.test(message)) {
    return pick(TOOL_RISK_REJECTIONS, message);
  }

  if (!EXPORT_SCOPE.test(message)) {
    return pick(TOOL_SCOPE_REJECTIONS, message);
  }

  return pick(TOOL_GENERIC_REJECTIONS, message);
}

function looksLikeDirectAttack(message) {
  if (SENSITIVE_TERMS.test(message) && QUESTION_OR_COMMAND.test(message)) {
    return true;
  }

  let hits = 0;
  for (const pattern of DIRECTIVE_PATTERNS) {
    if (pattern.test(message)) {
      hits += 1;
    }
  }

  return hits >= 2;
}

function isHintRequest(message) {
  return /\b(hint|tip|nudge)\b/i.test(message);
}

function composeTaskReply(message) {
  if (/\b(rewrite|rephrase|clearer tone|polish)\b/i.test(message)) {
    const content = contentAfterColon(message);

    if (!content) {
      return 'Paste the message you want rewritten. I will make it clearer, because apparently words enjoy wearing disguises.';
    }

    return `Here is a cleaner version:\n\n${cleanSentence(content)}\n\nTiny miracle: it now sounds like it was not assembled during a power outage.`;
  }

  if (/\b(summarize|summary|bullet points?)\b/i.test(message)) {
    const content = contentAfterColon(message);

    if (!content) {
      return 'Paste the text and I will summarize it into clean bullet points. Ideally text with actual content, a bold strategy.';
    }

    return `Summary:\n${summarizeToBullets(content)}`;
  }

  if (/\b(email|welcome email|draft)\b/i.test(message)) {
    return [
      'Subject: Welcome aboard',
      '',
      'Hi there,',
      '',
      'Welcome to the community. We are glad to have you here and look forward to seeing what you build, share, or bravely overthink with the rest of us.',
      '',
      'Best,',
      'Hack It Braw Team'
    ].join('\n');
  }

  return '';
}

function formatSuccessReply(secretValue, seed) {
  return pick(SUCCESS_REPLIES, seed).replace('{secret}', secretValue);
}

function isGreeting(message) {
  return /^(hi|hello|hey|yo|sup|good\s+(morning|afternoon|evening))[\s!.?]*$/i.test(message);
}

function scoreSuspicion(message) {
  let score = 30;

  for (const pattern of DIRECTIVE_PATTERNS) {
    if (pattern.test(message)) {
      score += 14;
    }
  }

  if (message.length > 240) {
    score += 12;
  }

  if (/["'`{}[\]]/.test(message)) {
    score += 8;
  }

  return Math.min(100, score);
}

function normalize(value) {
  return String(value || '').replace(/\r\n/g, '\n').trim();
}

function contentAfterColon(message) {
  const index = message.indexOf(':');

  if (index === -1) {
    return '';
  }

  return message.slice(index + 1).trim();
}

function cleanSentence(content) {
  const cleaned = content
    .replace(/\bu\b/gi, 'you')
    .replace(/\bur\b/gi, 'your')
    .replace(/\bpls\b/gi, 'please')
    .replace(/\bthx\b/gi, 'thanks')
    .replace(/\s+/g, ' ')
    .trim();

  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function summarizeToBullets(content) {
  const parts = content
    .split(/(?<=[.!?])\s+|\n+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 3);

  const bullets = parts.length ? parts : [content.trim()];
  return bullets.map((part) => `- ${cleanSentence(part)}`).join('\n');
}

function response({ event, reply, suspicion, solved = false }) {
  return {
    event,
    reply: solved ? reply : sanitizeOutput(reply),
    solved,
    suspicion: Math.max(0, Math.min(100, suspicion))
  };
}

function pick(items, seed) {
  const hash = Array.from(seed).reduce((total, char) => total + char.charCodeAt(0), 0);
  return items[hash % items.length];
}
