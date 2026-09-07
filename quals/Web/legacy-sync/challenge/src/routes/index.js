'use strict';

const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({
    name: 'Draft Sync API',
    version: '1.2.3',
    status: 'ok',
    docs: '/api/docs',
  });
});

router.get('/api/docs', (req, res) => {
  res.json({
    description: 'Internal note-sharing and draft synchronization service.',
    endpoints: [
      {
        method: 'POST',
        path: '/api/draft/save',
        description: 'Save a new draft.',
        body: { title: 'string', content: 'string' },
      },
      {
        method: 'GET',
        path: '/api/draft/:id',
        description: 'Retrieve a saved draft by ID.',
      },
    ],
  });
});

module.exports = router;
