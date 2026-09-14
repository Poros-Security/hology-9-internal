import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { InvoicePage, InvoiceRow, Vendor } from '../types';
import { rupiah, shortDate } from '../money';

@Component({
  selector: 'app-invoices',
  imports: [FormsModule, RouterLink],
  template: `
    <div class="head">
      <h1>Invoices</h1>
      <div class="spacer"></div>
      <a class="button quiet" href="/api/invoices.csv">Download CSV</a>
      <a class="button" routerLink="/invoices/new">New invoice</a>
    </div>

    <div class="panel pad filters">
      <div class="field">
        <label for="status">Status</label>
        <select id="status" [(ngModel)]="status" (ngModelChange)="reload(1)">
          <option value="">Any</option>
          @for (option of statuses; track option) { <option [value]="option">{{ option }}</option> }
        </select>
      </div>
      <div class="field">
        <label for="vendor">Vendor</label>
        <select id="vendor" [(ngModel)]="vendorId" (ngModelChange)="reload(1)">
          <option value="">Any</option>
          @for (vendor of vendors(); track vendor.id) { <option [value]="vendor.id">{{ vendor.name }}</option> }
        </select>
      </div>
      <div class="field">
        <label for="from">Submitted from</label>
        <input id="from" type="date" [(ngModel)]="from" (ngModelChange)="reload(1)" />
      </div>
      <div class="field">
        <label for="to">Until</label>
        <input id="to" type="date" [(ngModel)]="to" (ngModelChange)="reload(1)" />
      </div>
      @if (status || vendorId || from || to) {
        <button class="link" (click)="clear()">Clear filters</button>
      }
    </div>

    <div class="panel">
      @if (loaded() && !rows().length) {
        <div class="empty">
          <p>{{ filtered() ? 'No invoices match these filters.' : "You haven't submitted an invoice yet." }}</p>
          @if (!filtered()) { <a class="button quiet" routerLink="/invoices/new">New invoice</a> }
        </div>
      } @else {
        <table>
          <thead>
            <tr>
              <th>Number</th><th>Vendor</th><th>Status</th><th>Submitted</th><th class="num">Amount</th>
            </tr>
          </thead>
          <tbody>
            @for (invoice of rows(); track invoice.id) {
              <tr>
                <td class="ref"><a [routerLink]="['/invoices', invoice.id]">{{ invoice.number }}</a></td>
                <td>{{ invoice.vendor }}</td>
                <td><span class="status {{ invoice.status }}">{{ invoice.status }}</span></td>
                <td>{{ date(invoice.created_at) }}</td>
                <td class="num">{{ money(invoice.amount) }}</td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>

    @if (pages() > 1) {
      <div class="pager">
        <button class="quiet" [disabled]="page() === 1" (click)="reload(page() - 1)">Previous</button>
        <span>Page {{ page() }} of {{ pages() }}, {{ total() }} invoices</span>
        <button class="quiet" [disabled]="page() === pages()" (click)="reload(page() + 1)">Next</button>
      </div>
    }
  `,
})
export class InvoicesPage {
  private http = inject(HttpClient);

  protected readonly statuses = ['draft', 'submitted', 'approved', 'rejected'];
  protected status = '';
  protected vendorId = '';
  protected from = '';
  protected to = '';

  protected rows = signal<InvoiceRow[]>([]);
  protected vendors = signal<Vendor[]>([]);
  protected total = signal(0);
  protected page = signal(1);
  protected pages = signal(1);
  protected loaded = signal(false);

  protected money = rupiah;
  protected date = shortDate;

  constructor() {
    this.http.get<{ vendors: Vendor[] }>('/api/vendors').subscribe(result => this.vendors.set(result.vendors));
    this.reload(1);
  }

  filtered() {
    return Boolean(this.status || this.vendorId || this.from || this.to);
  }

  clear() {
    this.status = '';
    this.vendorId = '';
    this.from = '';
    this.to = '';
    this.reload(1);
  }

  reload(page: number) {
    const params: Record<string, string> = { page: String(page) };
    if (this.status) params['status'] = this.status;
    if (this.vendorId) params['vendor_id'] = this.vendorId;
    if (this.from) params['from'] = this.from;
    if (this.to) params['to'] = this.to;

    this.http.get<InvoicePage>('/api/invoices', { params })
      .subscribe(result => {
        this.rows.set(result.invoices);
        this.total.set(result.total);
        this.page.set(result.page);
        this.pages.set(result.pages);
        this.loaded.set(true);
      });
  }
}
