const express = require("express");
const cors = require("cors");
const path = require("path");
const rateLimit = require("express-rate-limit");
const { ApolloServer } = require("@apollo/server");
const { expressMiddleware } = require("@apollo/server/express4");
const { typeDefs } = require("./schema");
const { resolvers } = require("./resolvers");
const { getUserFromRequest } = require("./auth");
const { pool } = require("./db/connection");

async function start() {
  const app = express();
  const port = Number(process.env.PORT || 8011);

  app.disable("x-powered-by");
  app.use(express.static(path.join(__dirname, "../ui")));
  app.get("/healthz", (_, res) => res.json({ ok: true }));

  app.use(
    "/graphql",
    rateLimit({
      windowMs: 60 * 1000,
      limit: 240,
      standardHeaders: true,
      legacyHeaders: false
    })
  );

  const server = new ApolloServer({
    typeDefs,
    resolvers,
    introspection: false
  });

  await server.start();

  app.use(
    "/graphql",
    cors(),
    express.json({ limit: "32kb" }),
    expressMiddleware(server, {
      context: async ({ req }) => ({ user: await getUserFromRequest(req) })
    })
  );

  const httpServer = app.listen(port, "0.0.0.0", () => {
    console.log(`TaskForge listening on 0.0.0.0:${port}`);
  });

  async function shutdown() {
    httpServer.close(async () => {
      await server.stop();
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
