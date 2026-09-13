import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { InvoiceRow } from '../types';
import { rupiah, shortDate } from '../money';

@Component({
  selector: 'app-approvals',
  imports: [FormsModule, RouterLink],
  template: `
    <div class="head">
      <h1>Waiting for approval</h1>
      <div class="spacer"></div>
      <a class="button quiet" routerLink="/approvals/decided">Already decided</a>
    </div>

    @if (error()) { <div class="alert">{{ error() }}</div> }

    <div class="panel">
      @if (loaded() && !rows().length) {
        <div class="empty"><p>Nothing is waiting for approval.</p></div>
      } @else {
        <table>
          <thead>
            <tr>
              <th>Number</th><th>Vendor</th><th>Submitted by</th><th>Submitted</th>
              <th class="num">Amount</th><th>Note</th><th></th>
            </tr>
          </thead>
          <tbody>
            @for (invoice of rows(); track invoice.id) {
              <tr>
                <td class="ref">{{ invoice.number }}</td>
                <td>{{ invoice.vendor }}</td>
                <td>{{ invoice.submitted_by }}</td>
                <td>{{ date(invoice.created_at) }}</td>
                <td class="num">{{ money(invoice.amount) }}</td>
                <td><input name="n{{ invoice.id }}" [(ngModel)]="notes[invoice.id]" placeholder="Add a note" /></td>
                <td class="num">
                  <button (click)="decide(invoice, 'approved')">Approve</button>
                  <button class="quiet" (click)="decide(invoice, 'rejected')">Reject</button>
                </td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
})
export class ApprovalsPage {
  private http = inject(HttpClient);

  protected rows = signal<InvoiceRow[]>([]);
  protected loaded = signal(false);
  protected error = signal('');
  protected notes: Record<number, string> = {};

  protected money = rupiah;
  protected date = shortDate;

  constructor() {
    this.load();
  }

  load() {
    this.http.get<{ invoices: InvoiceRow[] }>('/api/approvals').subscribe({
      next: result => { this.rows.set(result.invoices); this.loaded.set(true); },
      error: failure => { this.error.set(failure.error?.error ?? 'Could not load.'); this.loaded.set(true); },
    });
  }

  decide(invoice: InvoiceRow, action: string) {
    this.http.post(`/api/approvals/${invoice.id}`, { action, note: this.notes[invoice.id] ?? '' }).subscribe({
      next: () => this.load(),
      error: failure => this.error.set(failure.error?.error ?? 'Could not save.'),
    });
  }
}
