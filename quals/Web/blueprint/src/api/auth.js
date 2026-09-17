const jwt = require("jsonwebtoken");
const { pool } = require("./db/connection");

const JWT_SECRET = process.env.JWT_SECRET || "local-dev-secret-change-me";

function signToken(user) {
  return jwt.sign(
    { sub: String(user.id), username: user.username },
    JWT_SECRET,
    { expiresIn: "2h" }
  );
}

async function getUserFromRequest(req) {
  const header = req.headers.authorization || "";
  const match = header.match(/^Bearer\s+(.+)$/i);
  if (!match) {
    return null;
  }

  try {
    const payload = jwt.verify(match[1], JWT_SECRET);
    const result = await pool.query(
      "SELECT id, username, role, bio FROM users WHERE id = $1",
      [payload.sub]
    );
    return result.rows[0] || null;
  } catch (_) {
    return null;
  }
}

module.exports = { signToken, getUserFromRequest };
