<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>HACK IT BRAW!</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: "Segoe UI", system-ui, sans-serif;
            background: radial-gradient(1200px 600px at 20% -10%, #16233f 0%, #0b1220 55%) #0b1220;
            color: #e8eefc;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px 48px;
            border-bottom: 1px solid #1f2c4a;
        }
        .brand { font-weight: 800; font-size: 1.15rem; letter-spacing: 2px; }
        .brand span { color: #ffb347; }
        .org { font-size: 0.8rem; color: #7c8db5; letter-spacing: 1px; }
        main {
            flex: 1;
            display: flex;
            justify-content: center;
            padding: 56px 20px;
        }
        .card {
            width: 100%;
            max-width: 560px;
            background: #111a2e;
            border: 1px solid #24365e;
            border-radius: 14px;
            padding: 36px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
        }
        .card h1 { font-size: 1.5rem; margin-bottom: 8px; }
        .card .sub { color: #8fa3cf; font-size: 0.95rem; line-height: 1.6; margin-bottom: 28px; }
        .card .sub code {
            background: #1c2a4a; color: #ffb347;
            padding: 1px 7px; border-radius: 4px;
            font-family: "Consolas", monospace; font-size: 0.85em;
        }
        form { display: flex; flex-direction: column; gap: 14px; }
        label { font-size: 0.85rem; font-weight: 600; color: #b9c6e8; letter-spacing: 0.5px; }
        input[type=file] {
            width: 100%;
            background: #0d1526;
            border: 1px dashed #3a4f82;
            border-radius: 8px;
            color: #e8eefc;
            padding: 14px;
            cursor: pointer;
        }
        input[type=file]::file-selector-button {
            background: #1c2a4a;
            border: 1px solid #31477a;
            color: #e8eefc;
            border-radius: 6px;
            padding: 8px 14px;
            margin-right: 12px;
            cursor: pointer;
            font-weight: 600;
        }
        button {
            background: #ffb347;
            border: none;
            border-radius: 8px;
            color: #0b1220;
            font-weight: 700;
            font-size: 1rem;
            padding: 13px;
            cursor: pointer;
            transition: background 0.15s;
        }
        button:hover { background: #ffc46b; }
        .msg {
            border-radius: 8px;
            padding: 13px 15px;
            margin-top: 18px;
            font-size: 0.9rem;
            word-break: break-all;
        }
        .msg.error { background: #3a1620; border: 1px solid #a33a4a; color: #ff9aa8; }
        .msg.success { background: #123220; border: 1px solid #2e8a52; color: #7df0a8; }
        .msg a { color: #ffb347; }
        .msg small { display: block; margin-top: 6px; color: #7c8db5; }
        footer {
            padding: 16px 48px;
            border-top: 1px solid #1f2c4a;
            font-size: 0.75rem;
            color: #55688f;
            display: flex;
            justify-content: space-between;
            gap: 20px;
        }
    </style>
</head>
<body>
<header>
    <div class="brand">HACK IT BRAW!<span>67</span></div>
    <div class="org">QUALIFIERS 2026</div>
</header>

<main>
    <div class="card">
        <h1>Upload your avatar</h1>
        <p class="sub">
            Before the quals begin, every team uploads a profile avatar for the leaderboard.
            Images only (GIF, JPEG, PNG) — our validator checks every file carefully.
            You'll get a direct link to your avatar when you're done.
        </p>

        <form method="POST" enctype="multipart/form-data">
            <label for="avatar">AVATAR IMAGE</label>
            <input type="file" id="avatar" name="avatar" required>
            <button type="submit">Upload avatar</button>
        </form>

        <?php if (isset($error)): ?>
            <div class="msg error"><?= esc($error) ?></div>
        <?php endif; ?>

        <?php if (isset($success)): ?>
            <div class="msg success">
                <?= esc($success) ?>
                <small>MIME: <?= esc($mime ?? '?') ?> &middot; Size: <?= esc((string)($size ?? 0)) ?> bytes
                    <?php if (isset($path)): ?>
                        <br>Your avatar: <a href="<?= esc($path, 'attr') ?>" target="_blank"><?= esc($path) ?></a>
                    <?php endif; ?>
                </small>
            </div>
        <?php endif; ?>
    </div>
</main>
</footer>
</body>
</html>
