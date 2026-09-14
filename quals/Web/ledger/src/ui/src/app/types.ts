export interface Person { id: number; username: string; name: string; role: string; }
export interface Vendor { id: number; name: string; tax_id: string; bank_account: string; }
export interface InvoiceRow {
  id: number; number: string; vendor: string; amount: number; status: string;
  created_at: string; internal_note?: string; submitted_by?: string;
}
export interface InvoicePage { invoices: InvoiceRow[]; total: number; page: number; pages: number; }
