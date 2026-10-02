document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const errorEl = document.getElementById("error");
  errorEl.textContent = "";

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password")
      })
    });
    const data = await res.json();
    if (!res.ok) {
      errorEl.textContent = data.error || "Login failed";
      return;
    }
    localStorage.setItem("token", data.token);
    window.location.href = "/index.html";
  } catch (err) {
    errorEl.textContent = "Network error";
  }
});
