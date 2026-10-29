import test from 'node:test';
import assert from 'node:assert/strict';
import { filterIssues, issueForLink, storeForLink } from '../src/pages/workbench/emagIssueFilter.mjs';

const issues = [
  { issue_id:'a', id:1, name:'Example cup', part_number:'SKU-A', reason:'invalid_price', general_stock:3, state:'pending' },
  { issue_id:'b', id:2, name:'Example box', part_number:'SKU-B', reason:'documentation_rejected', general_stock:0, state:'proposed' },
  { issue_id:'c', id:3, name:'Unknown', part_number:'SKU-C', reason:'blocked', general_stock:null, state:'pending' },
];

test('filters SKU, issue reason, stock and workflow state together', () => {
  assert.deepEqual(filterIssues(issues, {search:'sku-a', reason:'invalid_price', stock:'positive', state:'pending'}).map(x=>x.issue_id), ['a']);
  assert.deepEqual(filterIssues(issues, {search:'', reason:'all', stock:'unknown', state:'all'}).map(x=>x.issue_id), ['c']);
  assert.deepEqual(filterIssues(issues, {search:'', reason:'all', stock:'zero', state:'proposed'}).map(x=>x.issue_id), ['b']);
});

test('invalid stock is unknown and a deep link never falls back to another issue', () => {
  const rows=[{...issues[0], general_stock:-1}, {...issues[1], general_stock:'3'}];
  assert.equal(filterIssues(rows, {search:'', reason:'all', stock:'unknown', state:'all'}).length, 2);
  assert.equal(issueForLink(issues, 'missing'), null);
  assert.equal(issueForLink(issues, 'b').part_number, 'SKU-B');
});

test('explicit store and issue links never fall back to another store', () => {
  const stores=[{store_id:'first-ro'},{store_id:'second-ro'}];
  assert.equal(storeForLink(stores,'second-ro','b'), 'second-ro');
  assert.equal(storeForLink(stores,'missing-ro','b'), null);
  assert.equal(storeForLink(stores,null,'b'), null);
  assert.equal(storeForLink(stores,null,null), 'first-ro');
});
