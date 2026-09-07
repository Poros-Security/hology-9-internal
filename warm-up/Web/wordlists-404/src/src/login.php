<?php
session_start();
require_once 'includes/db.php';
require_once 'includes/jwt.php';

define('JWT_SECRET', getenv('JWT_SECRET') ?: 'by73W49ur1$');

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    
    if (empty($username) || empty($password)) {
        $error = 'Username and password are required';
    } else {
        $db = new SimpleDB();
        $user = $db->verifyUser($username, $password);
        
        if ($user) {
            // Generate JWT token
            $payload = [
                'user_id' => $user['id'],
                'username' => $user['username'],
                'role' => $user['role'],
                'iat' => time(),
                'exp' => time() + (60 * 60 * 24) // 24 hours
            ];
            
            $token = JWT::generate($payload, JWT_SECRET);
            
            // Set JWT as cookie
            setcookie('auth_token', $token, time() + (60 * 60 * 24), '/');
            
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['username'] = $user['username'];
            $_SESSION['role'] = $user['role'];
            
            header('Location: index.php');
            exit;
        } else {
            $error = 'Invalid username or password';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - TechCorp Indonesia</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <section class="auth-section">
        <div class="container">
            <div class="auth-box">
                <h1>Welcome Back</h1>
                <p class="auth-subtitle">Login to access your dashboard</p>
                
                <?php if ($error): ?>
                    <div class="alert alert-error"><?php echo htmlspecialchars($error); ?></div>
                <?php endif; ?>
                
                <form method="POST" action="login.php" class="auth-form">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required 
                               value="<?php echo htmlspecialchars($username ?? ''); ?>"
                               placeholder="Enter your username">
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required
                               placeholder="Enter your password">
                    </div>
                    
                    <button type="submit" class="btn-primary btn-full">Login</button>
                </form>
                
                <p class="auth-footer">
                    Don't have an account? <a href="register.php">Register here</a>
                </p>
            </div>
        </div>
    </section>

    <?php include 'includes/footer.php'; ?>
</body>
</html>
