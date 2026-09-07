<?php
session_start();
?>

<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - TechCorp Indonesia</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <section class="dashboard-section">
        <div class="container">
            <div class="dashboard-header">
                <h1>Welcome, <?php echo htmlspecialchars($user_data['username']); ?>!</h1>
                <p class="user-role">Role: <?php echo htmlspecialchars($user_data['role']); ?></p>
            </div>

            <div class="dashboard-content">
                <div class="booking-section">
                    <h2>Book an Appointment</h2>
                    
                    <?php if ($error): ?>
                        <div class="alert alert-error"><?php echo htmlspecialchars($error); ?></div>
                    <?php endif; ?>
                    
                    <?php if ($success): ?>
                        <div class="alert alert-success"><?php echo htmlspecialchars($success); ?></div>
                    <?php endif; ?>
                    
                    <form method="POST" class="booking-form">
                        <div class="form-group">
                            <label for="service">Select Service *</label>
                            <select id="service" name="service" required>
                                <option value="">Choose a service...</option>
                                <option value="IT Consulting">IT Consulting</option>
                                <option value="Business Solutions">Business Solutions</option>
                                <option value="Technical Support">Technical Support</option>
                                <option value="Training & Workshop">Training & Workshop</option>
                            </select>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="date">Appointment Date *</label>
                                <input type="date" id="date" name="date" required 
                                       min="<?php echo date('Y-m-d'); ?>">
                            </div>
                            
                            <div class="form-group">
                                <label for="time">Appointment Time *</label>
                                <select id="time" name="time" required>
                                    <option value="">Choose time...</option>
                                    <option value="09:00">09:00 AM</option>
                                    <option value="10:00">10:00 AM</option>
                                    <option value="11:00">11:00 AM</option>
                                    <option value="13:00">01:00 PM</option>
                                    <option value="14:00">02:00 PM</option>
                                    <option value="15:00">03:00 PM</option>
                                    <option value="16:00">04:00 PM</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="notes">Additional Notes</label>
                            <textarea id="notes" name="notes" rows="4" 
                                      placeholder="Tell us about your requirements..."></textarea>
                        </div>
                        
                        <button type="submit" name="book_appointment" class="btn-primary">Book Appointment</button>
                    </form>
                </div>

                <div class="appointments-list">
                    <h2>Your Appointments</h2>
                    <?php if (empty($appointments)): ?>
                        <p class="no-appointments">You haven't booked any appointments yet.</p>
                    <?php else: ?>
                        <div class="appointments-grid">
                            <?php foreach ($appointments as $apt): ?>
                                <div class="appointment-card">
                                    <h4><?php echo htmlspecialchars($apt['service']); ?></h4>
                                    <p><strong>Date:</strong> <?php echo htmlspecialchars($apt['appointment_date']); ?></p>
                                    <p><strong>Time:</strong> <?php echo htmlspecialchars($apt['appointment_time']); ?></p>
                                    <?php if (!empty($apt['notes'])): ?>
                                        <p><strong>Notes:</strong> <?php echo htmlspecialchars($apt['notes']); ?></p>
                                    <?php endif; ?>
                                    <p class="appointment-created">Booked on: <?php echo htmlspecialchars($apt['created_at']); ?></p>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </section>

    <?php include 'includes/footer.php'; ?>
</body>
</html>
