const loginForm = document.getElementById("login-form");
const loginSubmit = document.getElementById("login-submit");
const loginError = document.getElementById("login-error");

const LOGIN_MUTATION = `
  mutation Login($username: String!, $password: String!) {
    login(username: $username, password: $password) {
      token
      user {
        username
        role
        bio
      }
    }
  }
`;

function setLoginLoading(loading) {
  loginSubmit.disabled = loading;
  loginSubmit.querySelector(".button-label").hidden = loading;
  loginSubmit.querySelector(".button-loading").hidden = !loading;
}

function showLoginError(message) {
  loginError.textContent = message;
  loginError.hidden = false;
}

function hideLoginError() {
  loginError.hidden = true;
  loginError.textContent = "";
}

loginForm.addEventListener("submit", async event => {
  event.preventDefault();
  hideLoginError();

  const formData = new FormData(loginForm);
  const username = String(formData.get("username") || "").trim();
  const password = String(formData.get("password") || "");

  if (!username || !password) {
    showLoginError("Enter your username and password.");
    return;
  }

  setLoginLoading(true);

  try {
    const data = await request(LOGIN_MUTATION, { username, password });

    if (!data?.login?.token) {
      throw new Error("Sign in could not be completed.");
    }

    setToken(data.login.token);
    window.location.href = "/dashboard.html";
  } catch (error) {
    showLoginError(error.message || "Sign in failed. Please try again.");
    setLoginLoading(false);
  }
});