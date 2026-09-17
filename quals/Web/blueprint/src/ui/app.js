const TOKEN_KEY = "taskforge_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(query, variables = {}) {
  const headers = {
    "Content-Type": "application/json"
  };

  const token = getToken();

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch("/graphql", {
    method: "POST",
    headers,
    body: JSON.stringify({ query, variables })
  });

  let payload;

  try {
    payload = await response.json();
  } catch {
    throw new Error("Something went wrong. Please try again.");
  }

  if (!response.ok) {
    const error = new Error(payload?.errors?.[0]?.message || "Something went wrong. Please try again.");
    error.status = response.status;
    error.graphQLErrors = payload?.errors || [];
    throw error;
  }

  if (payload.errors?.length) {
    const error = new Error(payload.errors[0].message || "Something went wrong. Please try again.");
    error.status = response.status;
    error.graphQLErrors = payload.errors;
    throw error;
  }

  return payload.data;
}

function isUnauthorized(error) {
  if (error?.status === 401) {
    return true;
  }

  const messages = [
    ...(error?.graphQLErrors || []).map(item => item?.message || ""),
    error?.message || ""
  ].join(" ").toLowerCase();

  return messages.includes("unauthorized") ||
    messages.includes("unauthenticated") ||
    messages.includes("invalid token") ||
    messages.includes("expired token") ||
    messages.includes("authentication required");
}

function redirectToLogin() {
  clearToken();
  window.location.href = "/login.html";
}

function getInitial(value) {
  return String(value || "T").trim().charAt(0).toUpperCase() || "T";
}

function showToast(message, type = "") {
  const toast = document.getElementById("toast");

  if (!toast) {
    return;
  }

  toast.textContent = message;
  toast.className = `toast${type ? ` toast-${type}` : ""}`;
  toast.hidden = false;

  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => {
    toast.hidden = true;
  }, 3200);
}