<?php
require_once 'includes/db.php';

$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    $confirm_password = $_POST['confirm_password'] ?? '';
    
    if (empty($username) || empty($password)) {
        $error = 'Username and password are required';
    } elseif (strlen($username) < 3) {
        $error = 'Username must be at least 3 characters';
    } elseif (strlen($password) < 6) {
        $error = 'Password must be at least 6 characters';
    } elseif ($password !== $confirm_password) {
        $error = 'Passwords do not match';
    } else {
        $db = new SimpleDB();
        if ($db->userExists($username)) {
            $error = 'Username already exists';
        } else {
            $user = $db->createUser($username, $password);
            if ($user) {
                $success = 'Registration successful! Please login.';
            } else {
                $error = 'Registration failed. Please try again.';
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - TechCorp Indonesia</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <section class="auth-section">
        <div class="container">
            <div class="auth-box">
                <h1>Create Account</h1>
                <p class="auth-subtitle">Join TechCorp to access exclusive features</p>
                
                <?php if ($error): ?>
                    <div class="alert alert-error"><?php echo htmlspecialchars($error); ?></div>
                <?php endif; ?>
                
                <?php if ($success): ?>
                    <div class="alert alert-success">
                        <?php echo htmlspecialchars($success); ?>
                        <a href="login.php">Click here to login</a>
                    </div>
                <?php endif; ?>
                
                <form method="POST" action="register.php" class="auth-form">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required 
                               value="<?php echo htmlspecialchars($username ?? ''); ?>"
                               placeholder="Choose a username">
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required
                               placeholder="Minimum 6 characters">
                    </div>
                    
                    <div class="form-group">
                        <label for="confirm_password">Confirm Password</label>
                        <input type="password" id="confirm_password" name="confirm_password" required
                               placeholder="Re-enter your password">
                    </div>
                    
                    <button type="submit" class="btn-primary btn-full">Register</button>
                </form>
                
                <p class="auth-footer">
                    Already have an account? <a href="login.php">Login here</a>
                </p>
            </div>
        </div>
    </section>

    <?php include 'includes/footer.php'; ?>
</body>
</html>