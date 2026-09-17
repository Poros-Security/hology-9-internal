const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.DB_HOST || "127.0.0.1",
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || "taskforge",
  user: process.env.DB_USER || "taskforge",
  password: process.env.DB_PASSWORD || "taskforge",
  max: 10,
  idleTimeoutMillis: 30000
});

module.exports = { pool };
