const express = require("express");
const { pool } = require("../db/connection");
const { requireFinance } = require("./auth");

const router = express.Router();

// Intentionally vulnerable: raw string concatenation, zero sanitization.
// This is the "softball" stage of the challenge - do not add filtering here.
router.get("/search", requireFinance, async (req, res) => {
  const note = req.query.note || "";
  const query = `SELECT id, employee, amount, note, status FROM expense_reports WHERE note LIKE '%${note}%'`;

  try {
    const result = await pool.query(query);
    return res.json({ results: result.rows });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

module.exports = { router };
