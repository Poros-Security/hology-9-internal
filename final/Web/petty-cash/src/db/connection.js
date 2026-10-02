const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.DB_HOST || "127.0.0.1",
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || "ledger",
  user: process.env.DB_USER || "ledger",
  password: process.env.DB_PASSWORD || "ledger",
  max: 10,
  idleTimeoutMillis: 30000
});

module.exports = { pool };
