// database.js - Database management with SQLite
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

// Ensure db directory exists
const dbDir = path.join(__dirname, 'db');
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize database
const db = new Database(path.join(dbDir, 'ctf.db'));

// Enable foreign keys
db.pragma('foreign_keys = ON');

// Initialize database tables
function initDB() {
  // Create users table
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Create letters table
  db.exec(`
    CREATE TABLE IF NOT EXISTS letters (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      reason TEXT NOT NULL,
      status TEXT DEFAULT 'Pending Review',
      username TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
    )
  `);

  console.log('[DB] Database initialized');
}

// User operations
const userOps = {
  create: (username, password) => {
    const stmt = db.prepare('INSERT INTO users (username, password) VALUES (?, ?)');
    return stmt.run(username, password);
  },
  
  findByUsername: (username) => {
    const stmt = db.prepare('SELECT * FROM users WHERE username = ?');
    return stmt.get(username);
  },
  
  exists: (username) => {
    const stmt = db.prepare('SELECT COUNT(*) as count FROM users WHERE username = ?');
    const result = stmt.get(username);
    return result.count > 0;
  }
};

// Letter operations
const letterOps = {
  create: (name, reason, username) => {
    const stmt = db.prepare('INSERT INTO letters (name, reason, username) VALUES (?, ?, ?)');
    const result = stmt.run(name, reason, username);
    return result.lastInsertRowid;
  },
  
  findById: (id) => {
    const stmt = db.prepare('SELECT * FROM letters WHERE id = ?');
    return stmt.get(id);
  },
  
  findByUsername: (username) => {
    const stmt = db.prepare('SELECT * FROM letters WHERE username = ? ORDER BY created_at DESC');
    return stmt.all(username);
  },
  
  updateStatus: (id, status) => {
    const stmt = db.prepare('UPDATE letters SET status = ? WHERE id = ?');
    return stmt.run(status, id);
  },
  
  getAll: () => {
    const stmt = db.prepare('SELECT * FROM letters ORDER BY created_at DESC');
    return stmt.all();
  }
};

module.exports = {
  initDB,
  userOps,
  letterOps,
  db
};
