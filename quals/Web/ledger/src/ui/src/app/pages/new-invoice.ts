import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { Vendor } from '../types';
import { rupiah } from '../money';

@Component({
  selector: 'app-new-invoice',
  imports: [FormsModule, RouterLink],
  template: `
    <div class="head"><h1>New invoice</h1></div>

    <div class="panel pad">
      @if (error()) { <div class="alert">{{ error() }}</div> }

      <form (ngSubmit)="submit()">
        <div class="field">
          <label for="vendor">Vendor</label>
          <select id="vendor" name="vendor" [(ngModel)]="vendorId" required>
            <option value="" disabled>Choose a vendor</option>
            @for (vendor of vendors(); track vendor.id) { <option [value]="vendor.id">{{ vendor.name }}</option> }
          </select>
        </div>

        <div class="field">
          <label for="description">What this invoice covers</label>
          <input id="description" name="description" [(ngModel)]="description" required />
        </div>

        <div class="field">
          <label>Line items</label>
          <table>
            <tbody>
              @for (item of items(); track $index) {
                <tr>
                  <td><input name="d{{ $index }}" [(ngModel)]="item.description" placeholder="Description" /></td>
                  <td class="qty"><input name="q{{ $index }}" type="number" min="1" [(ngModel)]="item.qty" /></td>
                  <td class="price"><input name="p{{ $index }}" type="number" min="0" step="1000" [(ngModel)]="item.unit_price" /></td>
                  <td class="num price">{{ money(item.qty * item.unit_price) }}</td>
                  <td class="drop">
                    @if (items().length > 1) { <button type="button" class="link" (click)="dropLine($index)">Remove</button> }
                  </td>
                </tr>
              }
              <tr class="total">
                <td colspan="3">Total</td>
                <td class="num">{{ money(total()) }}</td>
                <td></td>
              </tr>
            </tbody>
          </table>
          <div class="actions">
            <button type="button" class="quiet" (click)="addLine()">Add line</button>
          </div>
        </div>

        <div class="actions">
          <button [disabled]="busy()">{{ busy() ? 'Submitting' : 'Submit for approval' }}</button>
          <a routerLink="/invoices">Cancel</a>
        </div>
      </form>
    </div>
  `,
})
export class NewInvoicePage {
  private http = inject(HttpClient);
  private router = inject(Router);

  protected vendors = signal<Vendor[]>([]);
  protected items = signal([{ description: '', qty: 1, unit_price: 0 }]);
  protected vendorId = '';
  protected description = '';
  protected error = signal('');
  protected busy = signal(false);

  protected money = rupiah;

  constructor() {
    this.http.get<{ vendors: Vendor[] }>('/api/vendors').subscribe(result => this.vendors.set(result.vendors));
  }

  total() {
    return this.items().reduce((sum, item) => sum + (Number(item.qty) || 0) * (Number(item.unit_price) || 0), 0);
  }

  addLine() {
    this.items.update(lines => [...lines, { description: '', qty: 1, unit_price: 0 }]);
  }

  dropLine(index: number) {
    this.items.update(lines => lines.filter((_, at) => at !== index));
  }

  submit() {
    this.busy.set(true);
    this.error.set('');

    this.http.post<{ id: number }>('/api/invoices', { vendor_id: Number(this.vendorId), description: this.description, items: this.items() })
      .subscribe({
        next: created => this.router.navigate(['/invoices', created.id]),
        error: failure => { this.error.set(failure.error?.error ?? 'Could not submit.'); this.busy.set(false); },
      });
  }
}
