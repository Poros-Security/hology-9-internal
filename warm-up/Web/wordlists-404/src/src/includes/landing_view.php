<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechCorp Indonesia - Professional Services</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <h1>TechCorp Professional Services</h1>
                <p>Your trusted partner for IT consulting and business solutions.</p>
                <a href="register.php" class="btn-primary">Get Started</a>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section class="services">
        <div class="container">
            <h2>Our Services</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>IT Consulting</h3>
                    <p>Expert advice on technology strategy and implementation.</p>
                </div>
                <div class="service-card">
                    <h3>Business Solutions</h3>
                    <p>Custom solutions tailored to your business needs.</p>
                </div>
                <div class="service-card">
                    <h3>Technical Support</h3>
                    <p>24/7 technical assistance for your critical systems.</p>
                </div>
                <div class="service-card">
                    <h3>Training & Workshop</h3>
                    <p>Professional training programs for your team.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Team Preview Section -->
    <section class="about">
        <div class="container">
            <h2>Meet Our Expert Team</h2>
            <p style="text-align: center; margin-bottom: 2rem; color: #666;">
                Our talented professionals are here to help you succeed.
            </p>
            <div style="text-align: center;">
                <a href="team.php" class="btn-primary">View Our Team</a>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="cta">
        <div class="container">
            <h2>Ready to Get Started?</h2>
            <p>Login or register to book your appointment today.</p>
            <a href="login.php" class="btn-secondary">Login Now</a>
        </div>
    </section>

    <?php include 'includes/footer.php'; ?>
</body>
</html>
