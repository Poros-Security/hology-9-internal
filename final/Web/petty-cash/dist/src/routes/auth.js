const express = require("express");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");
const { pool } = require("../db/connection");

const JWT_SECRET = process.env.JWT_SECRET || "local-dev-secret-change-me";

const router = express.Router();

function signToken(user) {
  return jwt.sign(
    { sub: String(user.id), username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: "4h" }
  );
}

async function getUserFromRequest(req) {
  const header = req.headers.authorization || "";
  const match = header.match(/^Bearer\s+(.+)$/i);
  const token = match ? match[1] : req.cookies && req.cookies.token;
  if (!token) {
    return null;
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    const result = await pool.query(
      "SELECT id, username, role FROM users WHERE id = $1",
      [payload.sub]
    );
    return result.rows[0] || null;
  } catch (_) {
    return null;
  }
}

function requireAuth(req, res, next) {
  if (!req.user) {
    return res.status(401).json({ error: "Authentication required" });
  }
  next();
}

function requireFinance(req, res, next) {
  if (!req.user || req.user.role !== "finance") {
    return res.status(403).json({ error: "Forbidden" });
  }
  next();
}

router.post("/login", async (req, res) => {
  const { username, password } = req.body || {};
  if (typeof username !== "string" || typeof password !== "string") {
    return res.status(400).json({ error: "username and password are required" });
  }

  const result = await pool.query(
    "SELECT id, username, password_hash, role FROM users WHERE username = $1",
    [username]
  );
  const user = result.rows[0];
  if (!user || !(await bcrypt.compare(password, user.password_hash))) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  const token = signToken(user);
  res.cookie("token", token, { httpOnly: true, sameSite: "lax" });
  return res.json({
    token,
    user: { id: user.id, username: user.username, role: user.role }
  });
});

router.post("/logout", (req, res) => {
  res.clearCookie("token");
  return res.json({ ok: true });
});

module.exports = { router, getUserFromRequest, requireAuth, requireFinance };
