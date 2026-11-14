export function formatDate(dateString) {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function formatConfidence(level) {
  const normalized = (level || 'medium').toLowerCase();
  switch (normalized) {
    case 'high':
      return { label: 'High Confidence', badgeClass: 'badge-high' };
    case 'low':
      return { label: 'Low Confidence', badgeClass: 'badge-low' };
    case 'medium':
    default:
      return { label: 'Medium Confidence', badgeClass: 'badge-medium' };
  }
}

export function formatSeverity(severity) {
  const normalized = (severity || 'medium').toLowerCase();
  switch (normalized) {
    case 'critical':
      return { label: 'Critical', badgeClass: 'severity-critical' };
    case 'high':
      return { label: 'High', badgeClass: 'severity-high' };
    case 'low':
      return { label: 'Low', badgeClass: 'severity-low' };
    case 'medium':
    default:
      return { label: 'Medium', badgeClass: 'severity-medium' };
  }
}

export function formatStatus(status) {
  const normalized = (status || 'new').toLowerCase();
  switch (normalized) {
    case 'resolved':
      return { label: 'Resolved', badgeClass: 'status-resolved' };
    case 'mitigated':
      return { label: 'Mitigated', badgeClass: 'status-mitigated' };
    case 'analyzed':
      return { label: 'Analyzed', badgeClass: 'status-analyzed' };
    case 'new':
    default:
      return { label: 'New', badgeClass: 'status-new' };
  }
}

export function truncateText(text, length = 120) {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
}
