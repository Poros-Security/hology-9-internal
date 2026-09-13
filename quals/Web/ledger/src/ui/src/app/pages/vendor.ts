import { Component, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { InvoiceRow, Vendor } from '../types';
import { rupiah, shortDate } from '../money';

@Component({
  selector: 'app-vendor',
  imports: [RouterLink],
  template: `
    @if (vendor(); as detail) {
      <div class="head"><a routerLink="/vendors">Vendors</a></div>

      <div class="panel doc">
        <header><h1>{{ detail.name }}</h1></header>
        <dl class="facts">
          <dt>Tax ID</dt><dd class="ref">{{ detail.tax_id }}</dd>
          <dt>Bank account</dt><dd class="ref">{{ detail.bank_account }}</dd>
        </dl>
      </div>

      <div class="panel">
        <h2>Your invoices from this vendor</h2>
        @if (rows().length) {
          <table>
            <thead>
              <tr><th>Number</th><th>Status</th><th>Submitted</th><th class="num">Amount</th></tr>
            </thead>
            <tbody>
              @for (invoice of rows(); track invoice.id) {
                <tr>
                  <td class="ref"><a [routerLink]="['/invoices', invoice.id]">{{ invoice.number }}</a></td>
                  <td><span class="status {{ invoice.status }}">{{ invoice.status }}</span></td>
                  <td>{{ date(invoice.created_at) }}</td>
                  <td class="num">{{ money(invoice.amount) }}</td>
                </tr>
              }
            </tbody>
          </table>
        } @else {
          <div class="empty"><p>You haven't raised an invoice from this vendor.</p></div>
        }
      </div>
    }
  `,
})
export class VendorPage {
  private http = inject(HttpClient);

  readonly id = input.required<string>();

  protected vendor = signal<Vendor | null>(null);
  protected rows = signal<InvoiceRow[]>([]);

  protected money = rupiah;
  protected date = shortDate;

  ngOnInit() {
    this.http.get<{ vendor: Vendor; invoices: InvoiceRow[] }>(`/api/vendors/${this.id()}`).subscribe(result => {
      this.vendor.set(result.vendor);
      this.rows.set(result.invoices);
    });
  }
}
