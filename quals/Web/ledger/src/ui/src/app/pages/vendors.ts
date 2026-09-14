import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { Vendor } from '../types';

@Component({
  selector: 'app-vendors',
  imports: [RouterLink],
  template: `
    <div class="head"><h1>Vendors</h1></div>

    <div class="panel">
      @if (rows().length) {
      <table>
        <thead>
          <tr><th>Name</th><th>Tax ID</th><th>Bank account</th></tr>
        </thead>
        <tbody>
          @for (vendor of rows(); track vendor.id) {
            <tr>
              <td><a [routerLink]="['/vendors', vendor.id]">{{ vendor.name }}</a></td>
              <td class="ref">{{ vendor.tax_id }}</td>
              <td class="ref">{{ vendor.bank_account }}</td>
            </tr>
          }
        </tbody>
      </table>
      } @else {
        <div class="empty"><p>No vendors have been set up yet.</p></div>
      }
    </div>
  `,
})
export class VendorsPage {
  private http = inject(HttpClient);

  protected rows = signal<Vendor[]>([]);

  constructor() {
    this.http.get<{ vendors: Vendor[] }>('/api/vendors').subscribe(result => this.rows.set(result.vendors));
  }
}
