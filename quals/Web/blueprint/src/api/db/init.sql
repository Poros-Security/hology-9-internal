CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TABLE IF EXISTS maintenance_logs;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'member',
  bio VARCHAR(255) DEFAULT ''
);

CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  owner_id INT REFERENCES users(id)
);

CREATE TABLE tasks (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  title VARCHAR(200) NOT NULL,
  status VARCHAR(20) DEFAULT 'todo',
  assignee_id INT REFERENCES users(id)
);

CREATE TABLE comments (
  id SERIAL PRIMARY KEY,
  task_id INT REFERENCES tasks(id),
  author_id INT REFERENCES users(id),
  body TEXT
);

CREATE TABLE maintenance_logs (
  id SERIAL PRIMARY KEY,
  executed_by VARCHAR(50),
  command TEXT,
  output TEXT,
  executed_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (username, password_hash, role, bio) VALUES
  ('alice', crypt('password123', gen_salt('bf')), 'lead', 'Keeps project boards tidy.'),
  ('bob', crypt('password123', gen_salt('bf')), 'member', 'Usually works on deployment checklists.'),
  ('carol', crypt('password123', gen_salt('bf')), 'member', 'Owns QA notes and release comments.');

INSERT INTO projects (name, owner_id) VALUES
  ('Migration Blueprint', 1),
  ('Internal Ops Cleanup', 1);

INSERT INTO tasks (project_id, title, status, assignee_id) VALUES
  (1, 'Finish GraphQL migration checklist', 'in_progress', 2),
  (1, 'Review task mutation permissions', 'todo', 3),
  (2, 'Document maintenance scripts', 'todo', 2);

INSERT INTO comments (task_id, author_id, body) VALUES
  (1, 1, 'Keep the public schema small until launch.'),
  (3, 2, 'Ops notes mention secret artifacts under /opt/app/secret/.');

INSERT INTO maintenance_logs (executed_by, command, output) VALUES
  ('system', 'startup_check', 'System initialized. Sensitive runtime artifacts are mounted under /opt/app/secret/ and should not be exposed via API.');

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO taskforge;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO taskforge;
