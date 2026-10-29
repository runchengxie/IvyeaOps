import test from 'node:test';
import assert from 'node:assert/strict';
import { dashboardMetrics } from '../src/pages/workbench/emagDashboardData.mjs';

test('dashboard only calculates totals from available nonnegative fields', () => {
  const data = { offers: [{ id: 1 }], issues: [
    { reason: 'invalid_price', general_stock: 3 },
    { reason: 'invalid_price', general_stock: null },
    { reason: 'documentation_rejected', general_stock: 0 },
  ], commercial_summary: { orders_fbe_count: 2, orders_seller_count: 0, invoice_count: 1,
    inventory: { general_stock_total: 3 } }, summary: { price_status_unknown: 2, documentation_status_unknown: 1, stock_unknown: 4 } };
  assert.deepEqual(dashboardMetrics(data), { offers: 1, orders: 2, stock: 3, invoices: 1,
    issueCount: 3, priceWithStock: 1, documentationRejected: 1, blocked: 0,
    priceUnknown: 2, documentationUnknown: 1, stockUnknown: 4 });
  const missing = dashboardMetrics({ ...data, commercial_summary: { orders_fbe_count: 2, inventory: {} } });
  assert.equal(missing.orders, null);
  assert.equal(missing.stock, null);
  assert.equal(missing.invoices, null);
});

test('invalid stock is not counted as positive inventory', () => {
  const result = dashboardMetrics({ offers: [], issues: [
    { reason: 'invalid_price', general_stock: '3' },
    { reason: 'invalid_price', general_stock: Infinity },
    { reason: 'invalid_price', general_stock: -1 },
  ] });
  assert.equal(result.priceWithStock, 0);
  assert.equal(result.orders, null);
  assert.equal(result.priceUnknown, null);
  assert.equal(result.documentationUnknown, null);
  assert.equal(result.stockUnknown, null);
});
