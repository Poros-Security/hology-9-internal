import { Routes } from '@angular/router';
import { financeOnly, staffOnly } from './guards';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'invoices' },
  { path: 'invoices', loadComponent: () => import('./pages/invoices').then(m => m.InvoicesPage) },
  { path: 'invoices/new', loadComponent: () => import('./pages/new-invoice').then(m => m.NewInvoicePage) },
  { path: 'invoices/:id', loadComponent: () => import('./pages/invoice').then(m => m.InvoicePage) },
  { path: 'vendors', loadComponent: () => import('./pages/vendors').then(m => m.VendorsPage) },
  { path: 'vendors/:id', loadComponent: () => import('./pages/vendor').then(m => m.VendorPage) },
  { path: 'approvals', canActivate: [financeOnly], loadComponent: () => import('./pages/approvals').then(m => m.ApprovalsPage) },
  { path: 'approvals/decided', canActivate: [financeOnly], loadComponent: () => import('./pages/decided').then(m => m.DecidedPage) },
  { path: 'profile', loadComponent: () => import('./pages/profile').then(m => m.ProfilePage) },
  { path: 'admin', canActivate: [staffOnly], loadComponent: () => import('./pages/admin').then(m => m.AdminPage) },
  { path: '**', redirectTo: 'invoices' },
];
