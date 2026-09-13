import { Component, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { InvoiceRow } from '../types';
import { rupiah, shortDate, stamp } from '../money';

const back = '/ops';

@Component({
  selector: 'app-admin',
  template: `
    <div class="head">
      <h1>Admin</h1>
      <div class="spacer"></div>
      <button class="quiet" (click)="toggleInternal()">
        {{ includeInternal() ? 'Hide internal notes' : 'Include internal notes' }}
      </button>
    </div>

    @if (error()) { <div class="alert">{{ error() }}</div> }

    <div class="panel">
      <h2>All invoices</h2>
      @if (rows().length) {
      <table>
        <thead>
          <tr>
            <th>Number</th><th>Vendor</th><th>Status</th><th>Submitted</th><th class="num">Amount</th>
            @if (includeInternal()) { <th>Internal note</th> }
          </tr>
        </thead>
        <tbody>
          @for (invoice of rows(); track invoice.id) {
            <tr>
              <td class="ref">{{ invoice.number }}</td>
              <td>{{ invoice.vendor }}</td>
              <td><span class="status {{ invoice.status }}">{{ invoice.status }}</span></td>
              <td>{{ date(invoice.created_at) }}</td>
              <td class="num">{{ money(invoice.amount) }}</td>
              @if (includeInternal()) { <td class="note">{{ invoice.internal_note }}</td> }
            </tr>
          }
        </tbody>
      </table>
      } @else {
        <div class="empty"><p>No invoices to show.</p></div>
      }
    </div>

    <div class="panel pad">
      <h2>Settings</h2>

      @if (imported()) { <div class="alert ok">Settings applied.</div> }

      @if (settings(); as current) {
        <dl class="facts">
          <dt>Company</dt><dd>{{ current.company.name }}</dd>
          <dt>Approval threshold</dt><dd class="ref">{{ money(current.approval.threshold) }}</dd>
          <dt>Export page size</dt><dd class="ref">{{ current.export.page_size }}</dd>
          <dt>Retention</dt><dd class="ref">{{ current.retention.days }} days</dd>
        </dl>
      }

      <form (submit)="upload($event)" class="actions">
        <input type="file" accept="application/json" (change)="pick($event)" />
        <button [disabled]="!file">Import settings</button>
      </form>
    </div>

    <div class="panel">
      <h2>People</h2>
      @if (people().length) {
        <table>
          <thead><tr><th>Name</th><th>Username</th><th>Role</th></tr></thead>
          <tbody>
            @for (person of people(); track person.id) {
              <tr><td>{{ person.full_name }}</td><td class="ref">{{ person.username }}</td><td>{{ person.role }}</td></tr>
            }
          </tbody>
        </table>
      } @else {
        <div class="empty"><p>No people to show.</p></div>
      }
    </div>

    <div class="panel">
      <h2>Recent activity</h2>
      @if (activity().length) {
        <ul class="log">
          @for (entry of activity(); track entry.created_at) {
            <li>
              <span class="when">{{ when(entry.created_at) }}</span>
              <span>{{ entry.actor }}</span>
              <span>{{ entry.action }} {{ entry.number }}</span>
            </li>
          }
        </ul>
      } @else {
        <div class="empty"><p>No approvals recorded yet.</p></div>
      }
    </div>
  `,
})
export class AdminPage {
  private http = inject(HttpClient);

  protected rows = signal<InvoiceRow[]>([]);
  protected settings = signal<any>(null);
  protected people = signal<any[]>([]);
  protected activity = signal<any[]>([]);
  protected includeInternal = signal(false);
  protected error = signal('');
  protected imported = signal(false);
  protected file: File | null = null;

  protected money = rupiah;
  protected date = shortDate;
  protected when = stamp;

  constructor() {
    this.load();
    this.http.get<any>(`${back}/settings`).subscribe({ next: result => this.settings.set(result), error: () => {} });
    this.http.get<{ users: any[] }>(`${back}/users`).subscribe({ next: result => this.people.set(result.users), error: () => {} });
    this.http.get<{ entries: any[] }>(`${back}/audit`).subscribe({ next: result => this.activity.set(result.entries), error: () => {} });
  }

  load() {
    this.http.get<{ invoices: InvoiceRow[] }>(`${back}/export`, { params: { includeInternal: this.includeInternal() } }).subscribe({
      next: result => this.rows.set(result.invoices),
      error: failure => this.error.set(failure.error?.error ?? 'Could not load.'),
    });
  }

  toggleInternal() {
    this.includeInternal.update(on => !on);
    this.load();
  }

  pick(event: Event) {
    this.file = (event.target as HTMLInputElement).files?.[0] ?? null;
  }

  upload(event: Event) {
    event.preventDefault();
    if (!this.file) return;

    this.error.set('');
    this.imported.set(false);

    const form = new FormData();
    form.append('file', this.file);

    this.http.post<any>(`${back}/settings/import`, form).subscribe({
      next: () => {
        this.imported.set(true);
        this.http.get<any>(`${back}/settings`).subscribe(result => this.settings.set(result));
      },
      error: failure => this.error.set(failure.error?.error ?? 'Could not import.'),
    });
  }
}
