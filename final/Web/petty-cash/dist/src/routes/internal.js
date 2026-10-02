const express = require("express");
const { exec } = require("child_process");
const rateLimit = require("express-rate-limit");
const { pool } = require("../db/connection");

const router = express.Router();

const ALLOWED_FORMATS = new Set(["csv", "xlsx", "json"]);

// Blacklist on `destination`: ;  |  &  `  $(  and any whitespace EXCEPT
// newline. `[^\S\n]` = "whitespace, but not newline" - this is what leaves
// the intended gap open (newline + ${IFS} both pass this filter untouched).
const BLOCKED_CHARS = /[;|&`]/;
const BLOCKED_WHITESPACE = /[^\S\n]/;
const BLOCKED_SUBSHELL = "$(";

function isBlockedDestination(destination) {
  if (BLOCKED_CHARS.test(destination)) return true;
  if (destination.includes(BLOCKED_SUBSHELL)) return true;
  if (BLOCKED_WHITESPACE.test(destination)) return true;
  return false;
}

async function logSync(destination, status, output) {
  await pool.query(
    "INSERT INTO sync_logs (destination, status, output) VALUES ($1, $2, $3)",
    [destination, status, output]
  );
}

router.use(
  rateLimit({
    windowMs: 60 * 1000,
    limit: 120,
    standardHeaders: true,
    legacyHeaders: false
  })
);

router.post("/export", express.json({ limit: "8kb" }), async (req, res) => {
  const providedKey = req.headers["x-api-key"];

  const configResult = await pool.query(
    "SELECT api_key FROM integration_configs WHERE service_name = 'accounting_sync' LIMIT 1"
  );
  const realKey = configResult.rows[0] && configResult.rows[0].api_key;

  if (!providedKey || !realKey || providedKey !== realKey) {
    return res.status(403).json({ error: "Forbidden" });
  }

  const { format, destination } = req.body || {};

  if (typeof format !== "string" || !ALLOWED_FORMATS.has(format)) {
    return res.status(400).json({ error: "Bad Request" });
  }

  if (typeof destination !== "string" || destination.length === 0) {
    return res.status(400).json({ error: "Bad Request" });
  }

  if (isBlockedDestination(destination)) {
    await logSync(destination, "rejected", "Rejected by policy");
    return res.status(400).json({ error: "Bad Request" });
  }

  const command = `/opt/app/src/scripts/export.sh ${format} ${destination}`;

  exec(command, { timeout: 5000, maxBuffer: 64 * 1024 }, async (err, stdout, stderr) => {
    try {
      if (err) {
        const output = `${stdout || ""}${stderr || ""}`.trim() || err.message;
        await logSync(destination, "error", output);
        return res.status(200).json({ status: "error", output });
      }
      const output = (stdout + stderr).trim();
      await logSync(destination, "ok", output);
      return res.status(200).json({ status: "ok", output });
    } catch (logErr) {
      return res.status(200).json({ status: "error", output: logErr.message });
    }
  });
});

module.exports = { router };
