const express = require("express");
const app = express();
const path = require("path");

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

app.use(express.json());

app.get("/", (req, res) => {
  res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Acme Config Generator</title>
            <style>
                body { font-family: sans-serif; padding: 2rem; background: #1e1e2e; color: #cdd6f4; }
                .container { max-width: 600px; margin: 0 auto; background: #181825; padding: 2rem; border-radius: 10px; }
                textarea { width: 100%; height: 150px; background: #313244; color: #a6e3a1; border: none; padding: 10px; border-radius: 5px; }
                button { margin-top: 10px; padding: 10px 20px; background: #89b4fa; color: #11111b; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Acme Config Generator (BETA)</h2>
                <p>Kirimkan konfigurasi kustom Anda dalam format JSON. Sistem akan menggabungkannya dengan konfigurasi default dan menyimpannya.</p>
                <form id="configForm">
                    <textarea id="jsonInput">{"theme": "dark", "language": "en"}</textarea>
                    <button type="submit">Generate Config</button>
                </form>
                <div id="result" style="margin-top: 20px;"></div>
            </div>
            <script>
                document.getElementById('configForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const resultDiv = document.getElementById('result');
                    try {
                        const payload = JSON.parse(document.getElementById('jsonInput').value);
                        const res = await fetch('/api/config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        resultDiv.innerHTML = await res.text();
                    } catch (err) {
                        resultDiv.innerText = "Error: Invalid JSON";
                    }
                });
            </script>
        </body>
        </html>
    `);
});

const setIn = require("set-in");

app.post("/api/config", (req, res) => {
  let defaultConfig = {
    theme: "light",
    language: "id",
    debug: false,
  };

  try {
    if (req.body && req.body.path && req.body.value) {
      setIn(defaultConfig, req.body.path, req.body.value);
    } else {
      for (let key in req.body) {
        if (key !== "path" && key !== "value") {
          defaultConfig[key] = req.body[key];
        }
      }
    }
  } catch (e) {
    return res.status(500).send("Error parsing configuration.");
  }

  res.render("config", { config: defaultConfig });
});

const port = 3000;
app.listen(port, () => {
  console.log(`Acme Config Generator listening on port ${port}`);
});
