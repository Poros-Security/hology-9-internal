CREATE TABLE users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  full_name     TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'employee',
  created_at    TEXT NOT NULL
);

CREATE TABLE vendors (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  tax_id       TEXT NOT NULL,
  bank_account TEXT NOT NULL
);

CREATE TABLE invoices (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  number        TEXT NOT NULL UNIQUE,
  user_id       INTEGER NOT NULL REFERENCES users(id),
  vendor_id     INTEGER NOT NULL REFERENCES vendors(id),
  amount        INTEGER NOT NULL,
  description   TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'draft',
  internal_note TEXT,
  created_at    TEXT NOT NULL,
  approved_at   TEXT
);

CREATE TABLE line_items (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id  INTEGER NOT NULL REFERENCES invoices(id),
  description TEXT NOT NULL,
  qty         INTEGER NOT NULL,
  unit_price  INTEGER NOT NULL
);

CREATE TABLE approvals (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id INTEGER NOT NULL REFERENCES invoices(id),
  actor_id   INTEGER NOT NULL REFERENCES users(id),
  action     TEXT NOT NULL,
  note       TEXT,
  created_at TEXT NOT NULL
);
