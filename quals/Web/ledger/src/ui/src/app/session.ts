import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Person } from './types';

@Injectable({ providedIn: 'root' })
export class Session {
  private http = inject(HttpClient);

  readonly person = signal<Person | null>(null);
  readonly checked = signal(false);

  readonly ready = firstValueFrom(this.http.get<Person>('/api/me')).then(
    person => this.settle(person),
    () => this.settle(null),
  );

  signIn(username: string, password: string) {
    return this.http.post<Person>('/api/login', { username, password });
  }

  hold(person: Person) {
    this.person.set(person);
  }

  release() {
    this.http.post('/api/logout', {}).subscribe(() => this.person.set(null));
  }

  private settle(person: Person | null) {
    this.person.set(person);
    this.checked.set(true);
    return person;
  }
}
