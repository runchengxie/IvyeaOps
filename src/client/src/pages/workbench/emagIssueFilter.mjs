/** Filter observations without treating missing or invalid stock as zero. */
export function filterIssues(issues, { search, reason, stock, state }) {
  const query = search.trim().toLocaleLowerCase();
  return issues.filter(issue => {
    const text = [issue.id, issue.name, issue.part_number, issue.part_number_key].filter(x => x != null).join(' ').toLocaleLowerCase();
    const value = issue.general_stock;
    const known = typeof value === 'number' && Number.isFinite(value) && value >= 0;
    const stockClass = !known ? 'unknown' : value > 0 ? 'positive' : 'zero';
    return (!query || text.includes(query)) && (reason === 'all' || issue.reason === reason)
      && (stock === 'all' || stockClass === stock) && (state === 'all' || issue.state === state);
  });
}

export function issueForLink(issues, issueId) {
  return issues.find(issue => issue.issue_id === issueId) ?? null;
}

export function storeForLink(stores, storeId, issueId) {
  if (storeId) return stores.some(store => store.store_id === storeId) ? storeId : null;
  if (issueId) return null;
  return stores[0]?.store_id ?? null;
}
