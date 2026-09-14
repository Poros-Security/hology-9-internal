import { Component, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { rupiah, shortDate, stamp } from '../money';

@Component({
  selector: 'app-invoice',
  imports: [RouterLink],
  template: `
    @if (error()) {
      <div class="alert">{{ error() }}</div>
      <a class="button quiet" routerLink="/invoices">Back to invoices</a>
    } @else if (invoice(); as detail) {
      <div class="head"><a routerLink="/invoices">Invoices</a></div>

      <div class="panel doc">
        <header>
          <h1 class="ref">{{ detail.number }}</h1>
          <span class="status {{ detail.status }}">{{ detail.status }}</span>
          <div class="spacer"></div>
          <span class="note">Submitted {{ date(detail.created_at) }}</span>
        </header>

        <dl class="facts">
          <dt>Vendor</dt><dd><a [routerLink]="['/vendors', detail.vendor_id]">{{ detail.vendor }}</a></dd>
          <dt>Tax ID</dt><dd class="ref">{{ detail.tax_id }}</dd>
          <dt>Bank account</dt><dd class="ref">{{ detail.bank_account }}</dd>
          <dt>Description</dt><dd>{{ detail.description }}</dd>
        </dl>
      </div>

      <div class="panel">
        <table>
          <thead>
            <tr><th>Item</th><th class="num">Qty</th><th class="num">Unit price</th><th class="num">Amount</th></tr>
          </thead>
          <tbody>
            @for (item of items(); track item.description) {
              <tr>
                <td>{{ item.description }}</td>
                <td class="num">{{ item.qty }}</td>
                <td class="num">{{ money(item.unit_price) }}</td>
                <td class="num">{{ money(item.qty * item.unit_price) }}</td>
              </tr>
            }
            <tr class="total">
              <td colspan="3">Total</td>
              <td class="num">{{ money(detail.amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel">
        <h2>History</h2>
        @if (history().length) {
          <ul class="log">
            @for (entry of history(); track entry.created_at) {
              <li>
                <span class="when">{{ when(entry.created_at) }}</span>
                <span>{{ entry.actor }}</span>
                <span>{{ entry.action }}{{ entry.note ? ' — ' + entry.note : '' }}</span>
              </li>
            }
          </ul>
        } @else {
          <div class="empty"><p>This invoice hasn't been submitted yet.</p></div>
        }
      </div>
    }
  `,
})
export class InvoicePage {
  private http = inject(HttpClient);

  readonly id = input.required<string>();

  protected invoice = signal<any>(null);
  protected items = signal<any[]>([]);
  protected history = signal<any[]>([]);
  protected error = signal('');

  protected money = rupiah;
  protected date = shortDate;
  protected when = stamp;

  ngOnInit() {
    this.http.get<any>(`/api/invoices/${this.id()}`).subscribe({
      next: result => {
        this.invoice.set(result.invoice);
        this.items.set(result.items);
        this.history.set(result.history);
      },
      error: failure => this.error.set(failure.error?.error ?? 'Invoice not found.'),
    });
  }
}
