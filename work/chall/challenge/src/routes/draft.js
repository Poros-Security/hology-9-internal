'use strict';

const express    = require('express');
const router     = express.Router();
const serializer = require('../utils/serializer');

const store = new Map();

router.post('/save', (req, res) => {
  const { title, content } = req.body;

  if (!title || !content) {
    return res.status(400).json({ error: 'Both title and content are required.' });
  }

  const id = Math.random().toString(36).slice(2, 11);
  store.set(id, { title, content, savedAt: new Date().toISOString() });

  return res.json({ success: true, id });
});

router.get('/:id', (req, res) => {
  const draft = store.get(req.params.id);
  if (!draft) return res.status(404).json({ error: 'Draft not found.' });
  return res.json(draft);
});

router.post('/preview', (req, res) => {
  const { data } = req.body;

  if (!data) {
    return res.status(400).json({ error: 'Missing required field: data' });
  }

  let draft;
  try {
    draft = serializer.decode(data);
  } catch (_) {
    return res.status(400).json({ error: 'Invalid draft encoding.' });
  }

  let preview = '';
  if (draft && draft.title)   preview += `<h1>${draft.title}</h1>`;
  if (draft && draft.content) preview += `<p>${draft.content}</p>`;

  if (draft && draft.formatter && typeof draft.formatter === 'function') {
    preview = draft.formatter(preview);
  }

  return res.json({ success: true, preview });
});

module.exports = router;
