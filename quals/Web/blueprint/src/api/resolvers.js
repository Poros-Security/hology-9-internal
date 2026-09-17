const { GraphQLError } = require("graphql");
const bcrypt = require("bcryptjs");
const { exec } = require("child_process");
const { promisify } = require("util");
const { pool } = require("./db/connection");
const { signToken } = require("./auth");

const execAsync = promisify(exec);
const BLOCKED_SCRIPT_CHARS = /[;|&`\n\r<>]/;

function requireUser(context) {
  if (!context.user) {
    throw new GraphQLError("Authentication required", {
      extensions: { code: "UNAUTHENTICATED" }
    });
  }
  return context.user;
}

async function logMaintenance(executedBy, command, output) {
  const result = await pool.query(
    `INSERT INTO maintenance_logs (executed_by, command, output)
     VALUES ($1, $2, $3)
     RETURNING id, executed_by, command, output, executed_at`,
    [executedBy, command, output]
  );
  return result.rows[0];
}

function mapMaintenanceLog(row) {
  return {
    id: row.id,
    executedBy: row.executed_by,
    command: row.command,
    output: row.output,
    executedAt: row.executed_at instanceof Date
      ? row.executed_at.toISOString()
      : String(row.executed_at)
  };
}

async function getUserById(id) {
  const result = await pool.query(
    "SELECT id, username, role, bio FROM users WHERE id = $1",
    [id]
  );
  return result.rows[0] || null;
}

const resolvers = {
  Query: {
    me: (_, __, context) => context.user,

    projects: async () => {
      const result = await pool.query("SELECT id, name, owner_id FROM projects ORDER BY id");
      return result.rows;
    },

    project: async (_, { id }) => {
      const result = await pool.query(
        "SELECT id, name, owner_id FROM projects WHERE id = $1",
        [id]
      );
      return result.rows[0] || null;
    },

    maintenanceLogs: async (_, __, context) => {
      const user = requireUser(context);
      if (user.role !== "admin") {
        throw new GraphQLError("Forbidden", { extensions: { code: "FORBIDDEN" } });
      }

      const result = await pool.query(
        `SELECT id, executed_by, command, output, executed_at
         FROM maintenance_logs
         ORDER BY id DESC
         LIMIT 25`
      );
      return result.rows.map(mapMaintenanceLog);
    }
  },

  Mutation: {
    login: async (_, { username, password }) => {
      const result = await pool.query(
        "SELECT id, username, password_hash, role, bio FROM users WHERE username = $1",
        [username]
      );
      const user = result.rows[0];
      if (!user || !(await bcrypt.compare(password, user.password_hash))) {
        throw new GraphQLError("Invalid credentials", {
          extensions: { code: "BAD_USER_INPUT" }
        });
      }

      return {
        token: signToken(user),
        user: {
          id: user.id,
          username: user.username,
          role: user.role,
          bio: user.bio
        }
      };
    },

    updateProfile: async (_, { bio, role }, context) => {
      const user = requireUser(context);
      const nextBio = bio === undefined ? user.bio : bio;
      const nextRole = role === undefined ? user.role : role;

      const result = await pool.query(
        `UPDATE users
         SET bio = $1, role = $2
         WHERE id = $3
         RETURNING id, username, role, bio`,
        [nextBio, nextRole, user.id]
      );
      return result.rows[0];
    },

    createTask: async (_, { projectId, title }, context) => {
      const user = requireUser(context);
      const result = await pool.query(
        `INSERT INTO tasks (project_id, title, assignee_id)
         VALUES ($1, $2, $3)
         RETURNING id, project_id, title, status, assignee_id`,
        [projectId, title, user.id]
      );
      return result.rows[0];
    },

    updateTaskStatus: async (_, { taskId, status }, context) => {
      requireUser(context);
      const result = await pool.query(
        `UPDATE tasks
         SET status = $1
         WHERE id = $2
         RETURNING id, project_id, title, status, assignee_id`,
        [status, taskId]
      );
      if (!result.rows[0]) {
        throw new GraphQLError("Task not found", { extensions: { code: "NOT_FOUND" } });
      }
      return result.rows[0];
    },

    addComment: async (_, { taskId, body }, context) => {
      const user = requireUser(context);
      const result = await pool.query(
        `INSERT INTO comments (task_id, author_id, body)
         VALUES ($1, $2, $3)
         RETURNING id, task_id, author_id, body`,
        [taskId, user.id, body]
      );
      return result.rows[0];
    },

    runMaintenanceTask: async (_, { script }, context) => {
      const user = requireUser(context);
      const command = `/opt/app/src/api/scripts/maintenance.sh ${script}`;

      if (user.role !== "admin") {
        await logMaintenance(user.username, command, "Forbidden");
        throw new GraphQLError("Forbidden", { extensions: { code: "FORBIDDEN" } });
      }

      if (BLOCKED_SCRIPT_CHARS.test(script)) {
        await logMaintenance(user.username, command, "Rejected by policy");
        throw new GraphQLError("Maintenance task rejected", {
          extensions: { code: "BAD_USER_INPUT" }
        });
      }

      try {
        const { stdout, stderr } = await execAsync(command, {
          timeout: 3000,
          maxBuffer: 64 * 1024
        });
        return mapMaintenanceLog(
          await logMaintenance(user.username, command, (stdout + stderr).trim())
        );
      } catch (err) {
        const output = `${err.stdout || ""}${err.stderr || ""}`.trim() || err.message;
        return mapMaintenanceLog(await logMaintenance(user.username, command, output));
      }
    }
  },

  Project: {
    owner: async (project) => getUserById(project.owner_id),
    tasks: async (project) => {
      const result = await pool.query(
        "SELECT id, project_id, title, status, assignee_id FROM tasks WHERE project_id = $1 ORDER BY id",
        [project.id]
      );
      return result.rows;
    }
  },

  Task: {
    assignee: async (task) => task.assignee_id ? getUserById(task.assignee_id) : null,
    comments: async (task) => {
      const result = await pool.query(
        "SELECT id, task_id, author_id, body FROM comments WHERE task_id = $1 ORDER BY id",
        [task.id]
      );
      return result.rows;
    }
  },

  Comment: {
    author: async (comment) => getUserById(comment.author_id)
  }
};

module.exports = { resolvers };
