CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TABLE IF EXISTS sync_logs;
DROP TABLE IF EXISTS integration_configs;
DROP TABLE IF EXISTS expense_reports;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'staff'
);

CREATE TABLE expense_reports (
  id SERIAL PRIMARY KEY,
  employee VARCHAR(100),
  amount NUMERIC(10,2),
  note TEXT,
  status VARCHAR(20) DEFAULT 'pending'
);

-- the pivot table: Stage 1's actual payload, not a flag
CREATE TABLE integration_configs (
  id SERIAL PRIMARY KEY,
  service_name VARCHAR(50),
  endpoint_path VARCHAR(100),
  api_key VARCHAR(64)
);

-- populated by Stage 3 calls (success or filtered-rejection); not required
-- for the solve, but gives participants a blind-progress signal
CREATE TABLE sync_logs (
  id SERIAL PRIMARY KEY,
  destination VARCHAR(255),
  status VARCHAR(20), -- 'ok' | 'rejected' | 'error'
  output TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (username, password_hash, role) VALUES
  ('jsmith', crypt('jsmith123', gen_salt('bf')), 'staff'),
  ('finance', crypt('finance123', gen_salt('bf')), 'finance'),
  ('admin', crypt(encode(gen_random_bytes(24), 'hex'), gen_salt('bf')), 'admin');

INSERT INTO expense_reports (employee, amount, note, status) VALUES
  ('J. Smith', 128.50, 'Client lunch at The Grove, receipt attached', 'approved'),
  ('J. Smith', 42.00, 'Taxi to airport for Q3 conference', 'approved'),
  ('R. Alvarez', 899.99, 'Hotel stay - 2 nights, SF offsite', 'approved'),
  ('R. Alvarez', 15.75, 'Parking validation, downtown office', 'pending'),
  ('T. Nguyen', 310.00, 'Team dinner after sprint demo', 'approved'),
  ('T. Nguyen', 67.20, 'Office supplies - notebooks and markers', 'rejected'),
  ('K. Patel', 1200.00, 'Annual conference registration fee', 'approved'),
  ('K. Patel', 54.30, 'Uber rides during onsite client visit', 'pending'),
  ('M. Chen', 220.00, 'Catering for quarterly all-hands', 'approved'),
  ('M. Chen', 18.90, 'Coffee and snacks for interview panel', 'approved'),
  ('S. Johnson', 450.00, 'Flight change fee, rescheduled client meeting', 'pending'),
  ('S. Johnson', 76.40, 'Printing and binding for board presentation', 'approved'),
  ('D. Lee', 33.00, 'Mileage reimbursement for site visit', 'approved'),
  ('D. Lee', 500.00, 'Vendor deposit for new laptop batch', 'rejected'),
  ('A. Garcia', 95.60, 'Client gift basket for renewal signing', 'approved'),
  ('A. Garcia', 29.15, 'Lunch meeting with prospective vendor', 'pending'),
  ('N. Brooks', 610.00, 'Training course - cloud certification', 'approved'),
  ('N. Brooks', 12.50, 'Toll charges for client visit', 'approved');

INSERT INTO integration_configs (service_name, endpoint_path, api_key) VALUES
  ('accounting_sync', '/internal/sync/export', encode(gen_random_bytes(16), 'hex'));

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ledger;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ledger;
