import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Session } from '../session';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  template: `
    <main class="signin">
      <div class="panel pad">
        <h1>Ledger</h1>
        <p class="where">Invoice approvals for PT Nusantara Cipta Mandiri.</p>

        @if (error()) { <div class="alert">{{ error() }}</div> }

        <form (ngSubmit)="submit()">
          <div class="field">
            <label for="username">Username</label>
            <input id="username" name="username" [(ngModel)]="username" autocomplete="username" required />
          </div>
          <div class="field">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" [(ngModel)]="password" autocomplete="current-password" required />
          </div>
          <div class="actions">
            <button [disabled]="busy()">{{ busy() ? 'Signing in' : 'Sign in' }}</button>
          </div>
        </form>
      </div>
    </main>
  `,
})
export class LoginPage {
  private session = inject(Session);

  protected username = '';
  protected password = '';
  protected error = signal('');
  protected busy = signal(false);

  submit() {
    this.busy.set(true);
    this.error.set('');

    this.session.signIn(this.username, this.password).subscribe({
      next: person => this.session.hold(person),
      error: failure => { this.error.set(failure.error?.error ?? 'Sign in failed.'); this.busy.set(false); },
    });
  }
}
