import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Session } from './session';

const allow = (role: string): CanActivateFn => async () => {
  const session = inject(Session);
  const router = inject(Router);

  if (!session.checked()) await session.ready;

  return session.person()?.role === role ? true : router.createUrlTree(['/invoices']);
};

export const staffOnly = allow('staff');
export const financeOnly = allow('finance');
