import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { languages } from '../src/agents/i18n/languages.js';

const root=new URL('../src/agents/i18n/locales/',import.meta.url);
function leaves(value,prefix='',result={}){
  for(const [key,item] of Object.entries(value)){
    const path=prefix?`${prefix}.${key}`:key;
    if(item&&typeof item==='object'&&!Array.isArray(item))leaves(item,path,result);
    else result[path]=item;
  }
  return result;
}
test('the supported language list exposes all existing locale directories',()=>{
  assert.deepEqual(languages.map(x=>x.value),['en','ko','zh-CN','ja','ru','de','tr','it']);
  assert.equal(new Set(languages.map(x=>x.value)).size,languages.length);
});
for(const file of fs.readdirSync(new URL('en/',root)).filter(x=>x.endsWith('.json'))){
  test(`${file}: zh-CN follows canonical English keys and interpolation tokens`,()=>{
    const en=leaves(JSON.parse(fs.readFileSync(new URL(`en/${file}`,root),'utf8')));
    const zh=leaves(JSON.parse(fs.readFileSync(new URL(`zh-CN/${file}`,root),'utf8')));
    assert.deepEqual(Object.keys(zh).sort(),Object.keys(en).sort());
    for(const key of Object.keys(en)){
      assert.equal(typeof zh[key],typeof en[key],key);
      const tokens=s=>String(s).match(/\{\{[^}]+\}\}/g)?.sort()||[];
      assert.deepEqual(tokens(zh[key]),tokens(en[key]),key);
    }
  });
}
