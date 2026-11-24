// The World Today — Tuesday, 24 November 2026.
// make.fun bounty news-image-20261124.
//
// What this program does: it ships the finished picture of the day's
// news (entry.png, drawn in-session by render.py from 50 stories that
// were verified firsthand against 24 Nov 2026) and copies it to the
// output directory the grader provides. Nothing is fetched, drawn or
// randomised at run time, so every run writes the exact same bytes.
//
// Run it outside the grader with:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, 'entry.png');
const targetDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const target = join(targetDir, 'entry.png');

// Fail loudly instead of shipping a half-written file: the image must
// exist beside this program and must start with the PNG signature.
const bytes = readFileSync(source);
const pngMagic = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const looksLikePng = pngMagic.every((b, i) => bytes[i] === b);
if (!looksLikePng || bytes.length === 0) {
  throw new Error('entry.png is missing or is not a PNG file');
}
// The gate allows at most 1 MiB and 1024x1024. Check the file size and
// the IHDR width/height (bytes 16-23, big-endian), and refuse to ship
// an oversized image. Also confirm the file ends with the PNG IEND
// chunk, so a truncated render never goes out as a whole image.
if (bytes.length > 1048576) {
  throw new Error(`entry.png is ${bytes.length} bytes, over the 1 MiB limit`);
}
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width > 1024 || height > 1024) {
  throw new Error(`entry.png is ${width}x${height}, over the 1024x1024 limit`);
}
const iend = bytes.subarray(bytes.length - 12);
const iendOk =
  iend.readUInt32BE(0) === 0 &&
  iend.toString('ascii', 4, 8) === 'IEND' &&
  iend.readUInt32BE(8) === 0xae426082;
if (!iendOk) {
  throw new Error('entry.png is truncated: missing the IEND chunk');
}
if (!existsSync(targetDir)) mkdirSync(targetDir, { recursive: true });
copyFileSync(source, target);
console.log(`copied entry.png (${bytes.length} bytes) to ${target}`);
