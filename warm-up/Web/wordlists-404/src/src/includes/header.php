<?php
if (!isset($_SESSION)) {
    session_start();
}
$is_logged_in = isset($_SESSION['user_id']);
$username = $is_logged_in ? $_SESSION['username'] : '';
?>
<header class="main-header">
    <div class="container">
        <nav class="navbar">
            <div class="logo">
                <a href="index.php">🏢 TechCorp</a>
            </div>
            <ul class="nav-menu">
                <li><a href="index.php">Home</a></li>
                <li><a href="team.php">Team</a></li>
                <?php if ($is_logged_in): ?>
                    <li><a href="logout.php">Logout (<?php echo htmlspecialchars($username); ?>)</a></li>
                <?php else: ?>
                    <li><a href="login.php">Login</a></li>
                    <li><a href="register.php">Register</a></li>
                <?php endif; ?>
            </ul>
        </nav>
    </div>
</header>