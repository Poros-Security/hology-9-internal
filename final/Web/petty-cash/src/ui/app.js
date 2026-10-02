const token = localStorage.getItem("token");
if (!token) {
  window.location.href = "/login.html";
}

function toLogin() {
  localStorage.removeItem("token");
  window.location.href = "/login.html";
}

async function logout() {
  try {
    await fetch("/api/logout", { method: "POST" });
  } catch (_) {
    // ignore network errors; clearing the local token is enough to log out
  }
  toLogin();
}

function renderRows(rows) {
  const tbody = document.querySelector("#results tbody");
  tbody.innerHTML = "";
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.id}</td><td>${row.employee}</td><td>${row.amount}</td><td>${row.note}</td><td><span class="status">${row.status}</span></td>`;
    tbody.appendChild(tr);
  }
}

async function search(note) {
  const errorEl = document.getElementById("error");
  errorEl.textContent = "";
  try {
    const res = await fetch(`/api/reports/search?note=${encodeURIComponent(note)}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.status === 401 || res.status === 403) {
      toLogin();
      return;
    }
    const data = await res.json();
    if (!res.ok) {
      errorEl.textContent = data.error || "Search failed";
      renderRows([]);
      return;
    }
    renderRows(data.results || []);
  } catch (err) {
    errorEl.textContent = "Network error";
  }
}

document.getElementById("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const note = new FormData(e.target).get("note") || "";
  search(note);
});

document.getElementById("logout").addEventListener("click", logout);

search("");
