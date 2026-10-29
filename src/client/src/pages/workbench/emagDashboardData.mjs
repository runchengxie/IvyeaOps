/** Derive only metrics supported by the collected snapshot. */
export function dashboardMetrics(data) {
  const count = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
  const commercial = data.commercial_summary;
  const fbe = count(commercial?.orders_fbe_count);
  const seller = count(commercial?.orders_seller_count);
  const issues = data.issues;
  return {
    offers: data.offers.length,
    orders: fbe === null || seller === null ? null : fbe + seller,
    stock: count(commercial?.inventory?.general_stock_total),
    invoices: count(commercial?.invoice_count),
    issueCount: issues.length,
    priceWithStock: issues.filter(issue => issue.reason === 'invalid_price' && count(issue.general_stock) > 0).length,
    documentationRejected: issues.filter(issue => issue.reason === 'documentation_rejected').length,
    blocked: issues.filter(issue => issue.reason === 'blocked').length,
    priceUnknown: count(data.summary?.price_status_unknown),
    documentationUnknown: count(data.summary?.documentation_status_unknown),
    stockUnknown: count(data.summary?.stock_unknown),
  };
}
