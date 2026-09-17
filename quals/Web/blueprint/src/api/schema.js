const typeDefs = `#graphql
  type User {
    id: ID!
    username: String!
    role: String!
    bio: String
  }

  type Project {
    id: ID!
    name: String!
    owner: User!
    tasks: [Task!]!
  }

  type Task {
    id: ID!
    title: String!
    status: String!
    assignee: User
    comments: [Comment!]!
  }

  type Comment {
    id: ID!
    body: String!
    author: User!
  }

  type AuthPayload {
    token: String!
    user: User!
  }

  type MaintenanceLog {
    id: ID!
    executedBy: String!
    command: String!
    output: String!
    executedAt: String!
  }

  type Query {
    me: User
    projects: [Project!]!
    project(id: ID!): Project
    maintenanceLogs: [MaintenanceLog!]!
  }

  type Mutation {
    login(username: String!, password: String!): AuthPayload!
    updateProfile(bio: String, role: String): User!
    createTask(projectId: ID!, title: String!): Task!
    updateTaskStatus(taskId: ID!, status: String!): Task!
    addComment(taskId: ID!, body: String!): Comment!
    runMaintenanceTask(script: String!): MaintenanceLog!
  }
`;

module.exports = { typeDefs };
