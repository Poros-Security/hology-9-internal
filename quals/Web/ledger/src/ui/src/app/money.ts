const numbers = new Intl.NumberFormat('id-ID');

export const rupiah = (amount: number) => `Rp ${numbers.format(amount ?? 0)}`;

export const shortDate = (iso: string) =>
  iso ? new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '';

export const stamp = (iso: string) =>
  iso ? new Date(iso).toLocaleString('id-ID', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
