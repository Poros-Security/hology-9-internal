<?php
session_start();
session_destroy();

// Clear JWT cookie
setcookie('auth_token', '', time() - 3600, '/');

header('Location: index.php');
exit;
?>
