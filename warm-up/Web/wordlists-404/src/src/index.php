<?php
session_start();
require_once 'includes/db.php';
require_once 'includes/jwt.php';

define('JWT_SECRET', getenv('JWT_SECRET') ?: 'by73W49ur1$');

// Check if user is logged in
$is_logged_in = isset($_SESSION['user_id']);

if ($is_logged_in) {
    // Show dashboard
    $user_data = null;
    
    if (isset($_COOKIE['auth_token'])) {
        $token = $_COOKIE['auth_token'];
        
        if (JWT::verify($token, JWT_SECRET)) {
            $user_data = JWT::decode($token);
        }
    }
    
    if (!$user_data) {
        // Fallback to session
        $user_data = [
            'user_id' => $_SESSION['user_id'],
            'username' => $_SESSION['username'],
            'role' => $_SESSION['role']
        ];
    }
    
    $success = '';
    $error = '';
    $db = new SimpleDB();
    
    // Handle appointment booking
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['book_appointment'])) {
        $service = $_POST['service'] ?? '';
        $date = $_POST['date'] ?? '';
        $time = $_POST['time'] ?? '';
        $notes = $_POST['notes'] ?? '';
        
        if (empty($service) || empty($date) || empty($time)) {
            $error = 'Please fill in all required fields';
        } else {
            if ($db->createAppointment($user_data['user_id'], $service, $date, $time, $notes)) {
                $success = 'Appointment booked successfully!';
            } else {
                $error = 'Failed to book appointment. Please try again.';
            }
        }
    }
    
    // Get user appointments
    $appointments = $db->getUserAppointments($user_data['user_id']);
    
    // Include dashboard view
    include 'includes/dashboard_view.php';
    
} else {
    // Show landing page
    include 'includes/landing_view.php';
}
?>
