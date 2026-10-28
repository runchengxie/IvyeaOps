import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism } from 'react-syntax-highlighter';
import katex from 'katex';

test('math and syntax highlighting render after dependency upgrades', () => {
  const math = renderToStaticMarkup(React.createElement(ReactMarkdown, { remarkPlugins: [remarkMath], rehypePlugins: [rehypeKatex] }, 'Inline $x^2$'));
  assert.match(math, /class="katex"/);
  assert.match(math, /<math/);
  const code = renderToStaticMarkup(React.createElement(Prism, { language: 'javascript' }, 'const answer = 42;'));
  assert.match(code, /answer/);
  assert.match(code, /token/);
});

test('math rendering keeps untrusted links disabled', () => {
  const output = katex.renderToString(String.raw`\href{javascript:alert(1)}{click}`, { trust: false, throwOnError: false });
  assert.doesNotMatch(output, /href="javascript:/i);
});
