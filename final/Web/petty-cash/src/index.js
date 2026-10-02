const express = require("express");
const path = require("path");
const cookieParser = require("cookie-parser");
const { pool } = require("./db/connection");
const { router: authRouter, getUserFromRequest } = require("./routes/auth");
const { router: reportsRouter } = require("./routes/reports");
const { router: internalRouter } = require("./routes/internal");

async function start() {
  const app = express();
  const port = Number(process.env.PORT || 8013);

  app.disable("x-powered-by");
  app.use(cookieParser());

  app.use(express.static(path.join(__dirname, "ui")));
  app.get("/", (_, res) => res.redirect("/login.html"));
  app.get("/healthz", (_, res) => res.json({ ok: true }));

  // Attach req.user for every request (used by the auth middleware below).
  app.use(async (req, _res, next) => {
    req.user = await getUserFromRequest(req);
    next();
  });

  app.use("/api", express.json({ limit: "8kb" }), authRouter);
  app.use("/api/reports", reportsRouter);

  // Hidden service-to-service endpoint: not linked from the frontend, not
  // mentioned in the challenge description. Only reachable with a valid
  // X-Api-Key leaked via the Stage 1 SQLi.
  app.use("/internal/sync", internalRouter);

  const httpServer = app.listen(port, "0.0.0.0", () => {
    console.log(`Ledger listening on 0.0.0.0:${port}`);
  });

  async function shutdown() {
    httpServer.close(async () => {
      await pool.end();
      process.exit(0);
    });
  }

  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);
}

start().catch((err) => {
  console.error(err);
  process.exit(1);
});
