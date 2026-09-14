import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LoginPage } from './pages/login';
import { Session } from './session';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LoginPage],
  template: `
    @if (session.checked()) {
      @if (session.person(); as person) {
        <div class="bar">
          <span class="mark">Ledger</span>
          <nav>
            <a routerLink="/invoices" routerLinkActive="on">Invoices</a>
            <a routerLink="/vendors" routerLinkActive="on">Vendors</a>
            @if (person.role === 'finance') {
              <a routerLink="/approvals" routerLinkActive="on">Approvals</a>
            }
            @if (person.role === 'staff') {
              <a routerLink="/admin" routerLinkActive="on">Admin</a>
            }
          </nav>
          <div class="who">
            <a routerLink="/profile">{{ person.name }}</a>
            <button class="link" (click)="session.release()">Sign out</button>
          </div>
        </div>
        <main><router-outlet /></main>
      } @else {
        <app-login />
      }
    }
  `,
})
export class App {
  protected session = inject(Session);
}
