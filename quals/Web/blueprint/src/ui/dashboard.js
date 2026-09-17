let currentUser = null;
let currentProjects = [];

async function loadMe() {
  const data = await request(`
    query {
      me {
        username
        role
        bio
      }
    }
  `);

  if (!data?.me) {
    throw new Error("Your session could not be loaded.");
  }

  currentUser = data.me;

  document.getElementById("sidebar-username").textContent = currentUser.username;
  document.getElementById("sidebar-role").textContent = currentUser.role || "Member";
  document.getElementById("sidebar-avatar").textContent = getInitial(currentUser.username);
  document.getElementById("greeting").textContent = `Good to see you, ${currentUser.username}.`;
  document.getElementById("profile-username").textContent = currentUser.username;
  document.getElementById("profile-role").textContent = currentUser.role || "Member";
  document.getElementById("profile-avatar").textContent = getInitial(currentUser.username);
  document.getElementById("bio").value = currentUser.bio || "";
}

function normalizeStatus(status) {
  return String(status || "unknown").trim().toLowerCase().replace(/[_\s]+/g, "-");
}

function statusLabel(status) {
  const normalized = normalizeStatus(status);

  return normalized
    .split("-")
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Unknown";
}

function renderStats(projects) {
  const taskCount = projects.reduce((total, project) => total + (project.tasks?.length || 0), 0);

  document.getElementById("project-count").textContent = projects.length;
  document.getElementById("task-count").textContent = taskCount;
  document.getElementById("stat-synced").textContent = `Updated ${new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date())}`;
}

function createTaskRow(task) {
  const row = document.createElement("div");
  row.className = "task-row";

  const title = document.createElement("span");
  title.className = "task-title";
  title.textContent = task.title || "Untitled task";

  const status = document.createElement("span");
  const normalized = normalizeStatus(task.status);
  status.className = `task-status status-${normalized}`;
  status.textContent = statusLabel(task.status);

  const assignee = document.createElement("span");
  assignee.className = "task-assignee";
  assignee.textContent = task.assignee?.username || "Unassigned";

  row.append(title, status, assignee);
  return row;
}

function createProject(project) {
  const article = document.createElement("article");
  article.className = "project";

  const head = document.createElement("div");
  head.className = "project-head";

  const details = document.createElement("div");

  const name = document.createElement("h3");
  name.className = "project-name";
  name.textContent = project.name || "Untitled project";

  const meta = document.createElement("div");
  meta.className = "project-meta";

  const owner = document.createElement("span");
  owner.textContent = `Owner: ${project.owner?.username || "Unknown"}`;

  const id = document.createElement("span");
  id.className = "project-id";
  id.textContent = `ID ${project.id}`;

  meta.append(owner, id);
  details.append(name, meta);

  const count = document.createElement("span");
  count.className = "project-task-count";
  count.textContent = `${project.tasks?.length || 0} ${(project.tasks?.length || 0) === 1 ? "task" : "tasks"}`;

  head.append(details, count);
  article.append(head);

  const tasks = document.createElement("div");
  tasks.className = "task-list";

  if (!project.tasks?.length) {
    const empty = document.createElement("div");
    empty.className = "empty-block";
    empty.textContent = "No tasks in this project yet.";
    tasks.append(empty);
  } else {
    project.tasks.forEach(task => tasks.append(createTaskRow(task)));
  }

  article.append(tasks);
  article.append(createTaskForm(project.id));
  return article;
}

function createTaskForm(projectId) {
  const form = document.createElement("form");
  form.className = "create-task";
  form.dataset.projectId = projectId;

  const idInput = document.createElement("input");
  idInput.type = "text";
  idInput.value = projectId;
  idInput.readOnly = true;
  idInput.setAttribute("aria-label", "Project ID");

  const titleInput = document.createElement("input");
  titleInput.type = "text";
  titleInput.name = "title";
  titleInput.placeholder = "Add a task";
  titleInput.maxLength = 200;
  titleInput.required = true;
  titleInput.setAttribute("aria-label", "Task title");

  const button = document.createElement("button");
  button.className = "button button-dark";
  button.type = "submit";
  button.textContent = "Add task";

  form.append(idInput, titleInput, button);
  form.addEventListener("submit", handleCreateTask);
  return form;
}

function renderProjects(projects) {
  const list = document.getElementById("project-list");
  const status = document.getElementById("project-status");

  list.replaceChildren();

  if (!projects.length) {
    const empty = document.createElement("div");
    empty.className = "empty-block";
    empty.textContent = "No projects are available for this workspace.";
    list.append(empty);
    status.textContent = "";
    return;
  }

  projects.forEach(project => list.append(createProject(project)));
  status.textContent = `${projects.length} ${projects.length === 1 ? "project" : "projects"}`;
}

async function loadProjects() {
  const data = await request(`
    query {
      projects {
        id
        name
        owner {
          username
        }
        tasks {
          id
          title
          status
          assignee {
            username
          }
        }
      }
    }
  `);

  currentProjects = data?.projects || [];
  renderStats(currentProjects);
  renderProjects(currentProjects);
}

async function refreshWorkspace() {
  const button = document.getElementById("refresh-button");
  const label = button.querySelector(".refresh-label");

  button.disabled = true;
  label.textContent = "Refreshing…";

  try {
    await Promise.all([loadMe(), loadProjects()]);
    showToast("Workspace refreshed.");
  } catch (error) {
    if (isUnauthorized(error)) {
      redirectToLogin();
      return;
    }

    showToast(error.message || "Could not refresh the workspace.", "error");
  } finally {
    button.disabled = false;
    label.textContent = "Refresh";
  }
}

async function handleCreateTask(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const projectId = form.dataset.projectId;
  const titleInput = form.querySelector('input[name="title"]');
  const button = form.querySelector("button");
  const title = titleInput.value.trim();

  if (!title) {
    titleInput.focus();
    return;
  }

  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Adding…";

  try {
    await request(`
      mutation CreateTask($projectId: ID!, $title: String!) {
        createTask(projectId: $projectId, title: $title) {
          id
          title
        }
      }
    `, { projectId, title });

    titleInput.value = "";
    await loadProjects();
    showToast("Task added.");
  } catch (error) {
    if (isUnauthorized(error)) {
      redirectToLogin();
      return;
    }

    showToast(error.message || "Could not add the task.", "error");
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

async function handleProfileSubmit(event) {
  event.preventDefault();

  const button = document.getElementById("profile-submit");
  const message = document.getElementById("profile-message");
  const bio = document.getElementById("bio").value;

  button.disabled = true;
  button.textContent = "Saving…";
  message.hidden = true;

  try {
    const data = await request(`
      mutation UpdateProfile($bio: String) {
        updateProfile(bio: $bio) {
          username
          role
          bio
        }
      }
    `, { bio });

    currentUser = data.updateProfile;
    document.getElementById("bio").value = currentUser.bio || "";
    message.textContent = "Changes saved.";
    message.className = "form-message form-message-success";
    message.hidden = false;
  } catch (error) {
    if (isUnauthorized(error)) {
      redirectToLogin();
      return;
    }

    message.textContent = error.message || "Could not save your changes.";
    message.className = "form-message form-message-error";
    message.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "Save changes";
  }
}

function setupNavigation() {
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("nav-toggle");

  toggle.addEventListener("click", () => {
    const open = sidebar.classList.toggle("nav-open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  sidebar.querySelectorAll(".side-nav-link").forEach(link => {
    link.addEventListener("click", () => {
      sidebar.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

function setupSignOut() {
  document.getElementById("sign-out").addEventListener("click", () => {
    clearToken();
    window.location.href = "/";
  });
}

async function initialize() {
  if (!getToken()) {
    redirectToLogin();
    return;
  }

  try {
    await Promise.all([loadMe(), loadProjects()]);
  } catch (error) {
    if (isUnauthorized(error)) {
      redirectToLogin();
      return;
    }

    document.getElementById("project-list").innerHTML = "";
    const message = document.createElement("div");
    message.className = "empty-block";
    message.textContent = error.message || "The workspace could not be loaded.";
    document.getElementById("project-list").append(message);
    showToast("The workspace could not be loaded.", "error");
  }
}

document.getElementById("refresh-button").addEventListener("click", refreshWorkspace);
document.getElementById("profile-form").addEventListener("submit", handleProfileSubmit);
setupNavigation();
setupSignOut();
initialize();