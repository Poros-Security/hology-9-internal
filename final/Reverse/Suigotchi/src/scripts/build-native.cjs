const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

if (process.platform !== 'linux') {
  throw new Error('The included native build script currently targets Linux.');
}

const root = path.resolve(__dirname, '..');
const includeDir = path.join(path.dirname(require.resolve('node-api-headers/package.json')), 'include');
const outputDir = path.join(root, 'build', 'Release');
const output = path.join(outputDir, 'suigotchi.node');
fs.mkdirSync(outputDir, { recursive: true });

execFileSync('g++', [
  '-std=c++17',
  '-O2',
  '-fPIC',
  '-shared',
  '-fvisibility=hidden',
  '-fdata-sections',
  '-ffunction-sections',
  '-DNAPI_VERSION=8',
  '-DNODE_GYP_MODULE_NAME=suigotchi',
  `-I${includeDir}`,
  path.join(root, 'native', 'suigotchi.cpp'),
  '-Wl,--gc-sections',
  '-Wl,--strip-all',
  '-o',
  output,
], { stdio: 'inherit' });

console.log(`Built ${path.relative(root, output)}`);
