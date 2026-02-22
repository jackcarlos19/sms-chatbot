/** Build display name from nullable first/last, fallback to phone */
export function displayName(contact: { first_name: string | null; last_name: string | null; phone_number?: string }): string {
  const parts = [contact.first_name || '', contact.last_name || ''].filter(Boolean);
  const name = parts.join(' ').trim();
  return name || contact.phone_number || 'Unknown';
}

/** Format ISO datetime to readable string */
export function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

/** Format ISO datetime to short date */
export function formatShortDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString();
}

/** Format ISO datetime to time only */
export function formatTime(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
