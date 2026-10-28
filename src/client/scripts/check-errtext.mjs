#!/usr/bin/env node
/** Prevent rendering backend detail objects as React children.
 * Existing exemptions: the formatter, API interceptor and vendored Agents UI.
 * Keep this gate strict. Use fileURLToPath for native Windows paths.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL("../src", import.meta.url));
const SKIP_DIRS = new Set(["agents", "node_modules", "dist"]);
const ALLOW = new Set(["lib/errText.ts", "api/client.ts"]);
const PATTERN = /\.response\s*\??\.\s*data\s*\??\.\s*detail/;

/** @param {string} dir @param {string[]} out */
function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      if (!SKIP_DIRS.has(name)) walk(p, out);
    } else if (/\.tsx?$/.test(name) && !name.endsWith(".d.ts")) {
      out.push(p);
    }
  }
  return out;
}

const hits = [];
for (const file of walk(ROOT)) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  if (ALLOW.has(rel)) continue;
  readFileSync(file, "utf8").split("\n").forEach((line, i) => {
    if (PATTERN.test(line)) hits.push(`${rel}:${i + 1}  ${line.trim().slice(0, 100)}`);
  });
}

if (hits.length) {
  console.error(
    `\nFound ${hits.length} direct backend detail reads:\n\n` + hits.join("\n") +
    `\n\nUse errText(err, fallback) from src/lib/errText.ts.\n` +
    `FastAPI validation detail can be an object array and cannot be rendered directly.\n`);
  process.exit(1);
}
console.log('Backend error text contract passed.');
