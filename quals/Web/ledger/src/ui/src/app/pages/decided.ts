import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { rupiah, shortDate } from '../money';

@Component({
  selector: 'app-decided',
  imports: [RouterLink],
  template: `
    <div class="head">
      <h1>Already decided</h1>
      <div class="spacer"></div>
      <a class="button quiet" routerLink="/approvals">Waiting for approval</a>
    </div>

    @if (error()) { <div class="alert">{{ error() }}</div> }

    <div class="panel">
      @if (loaded() && !rows().length) {
        <div class="empty"><p>Nothing has been approved or rejected yet.</p></div>
      } @else {
        <table>
          <thead>
            <tr>
              <th>Number</th><th>Vendor</th><th>Submitted by</th><th>Decided</th>
              <th>By</th><th class="num">Amount</th><th>Status</th><th>Note</th>
            </tr>
          </thead>
          <tbody>
            @for (invoice of rows(); track invoice.id) {
              <tr>
                <td class="ref">{{ invoice.number }}</td>
                <td>{{ invoice.vendor }}</td>
                <td>{{ invoice.submitted_by }}</td>
                <td>{{ date(invoice.approved_at) }}</td>
                <td>{{ invoice.decided_by }}</td>
                <td class="num">{{ money(invoice.amount) }}</td>
                <td><span class="status {{ invoice.status }}">{{ invoice.status }}</span></td>
                <td class="note">{{ invoice.note }}</td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
})
export class DecidedPage {
  private http = inject(HttpClient);

  protected rows = signal<any[]>([]);
  protected loaded = signal(false);
  protected error = signal('');

  protected money = rupiah;
  protected date = shortDate;

  constructor() {
    this.http.get<{ invoices: any[] }>('/api/approvals/decided').subscribe({
      next: result => { this.rows.set(result.invoices); this.loaded.set(true); },
      error: failure => { this.error.set(failure.error?.error ?? 'Could not load.'); this.loaded.set(true); },
    });
  }
}
