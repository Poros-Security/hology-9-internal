import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Session } from '../session';

@Component({
  selector: 'app-profile',
  imports: [FormsModule],
  template: `
    <div class="head"><h1>Profile</h1></div>

    <div class="panel doc">
      @if (session.person(); as person) {
        <dl class="facts">
          <dt>Name</dt><dd>{{ person.name }}</dd>
          <dt>Username</dt><dd class="ref">{{ person.username }}</dd>
          <dt>Role</dt><dd>{{ person.role }}</dd>
        </dl>
      }
    </div>

    <div class="panel pad">
      <h2>Change password</h2>

      @if (error()) { <div class="alert">{{ error() }}</div> }
      @if (done()) { <div class="alert ok">Your password has been changed.</div> }

      <form (ngSubmit)="submit()">
        <div class="field">
          <label for="current">Current password</label>
          <input id="current" name="current" type="password" [(ngModel)]="current" autocomplete="current-password" required />
        </div>
        <div class="field">
          <label for="replacement">New password</label>
          <input id="replacement" name="replacement" type="password" [(ngModel)]="replacement" autocomplete="new-password" minlength="8" required />
        </div>
        <div class="actions">
          <button [disabled]="busy()">Change password</button>
        </div>
      </form>
    </div>
  `,
})
export class ProfilePage {
  private http = inject(HttpClient);
  protected session = inject(Session);

  protected current = '';
  protected replacement = '';
  protected error = signal('');
  protected done = signal(false);
  protected busy = signal(false);

  submit() {
    this.busy.set(true);
    this.error.set('');
    this.done.set(false);

    this.http.post('/api/profile/password', { current: this.current, replacement: this.replacement }).subscribe({
      next: () => {
        this.done.set(true);
        this.busy.set(false);
        this.current = '';
        this.replacement = '';
      },
      error: failure => { this.error.set(failure.error?.error ?? 'Could not change it.'); this.busy.set(false); },
    });
  }
}
