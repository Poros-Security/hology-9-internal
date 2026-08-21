'use strict';

const fs = require('fs');
const path = require('path');
const express = require('express');
const app = express();

if (!process.mainModule) {
  process.mainModule = require.main || module;
}

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const publicDir = path.join(__dirname, 'public');
const distDir = path.join(__dirname, '..', 'dist');

app.use(express.static(publicDir));
app.use(express.static(distDir));

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.use('/', require('./routes/index'));
app.use('/api/draft', require('./routes/draft'));

app.get('/', (req, res) => {
  const builtIndex = path.join(distDir, 'index.html');
  const rootIndex = path.join(__dirname, '..', 'index.html');

  if (fs.existsSync(builtIndex)) {
    return res.sendFile(builtIndex);
  }

  if (fs.existsSync(rootIndex)) {
    return res.sendFile(rootIndex);
  }

  return res.status(404).send('Frontend entrypoint not found');
});

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

const PORT = Number(process.env.PORT || 3000);

if (require.main === module) {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[*] Draft Sync API listening on port ${PORT}`);
  });
}

module.exports = app;
