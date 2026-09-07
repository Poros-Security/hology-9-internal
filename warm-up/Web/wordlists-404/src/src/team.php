<?php
session_start();

$employees = [
    [
        'id' => 1,
        'first_name' => 'Budi',
        'last_name' => 'Santoso',
        'nickname' => 'Bud',
        'birthdate' => '1985-03-15',
        'wife_name' => 'Siti',
        'position' => 'CEO & Founder',
        'hobby' => 'Photography'
    ],
    [
        'id' => 2,
        'first_name' => 'Andi',
        'last_name' => 'Wijaya',
        'nickname' => 'Andy',
        'birthdate' => '1990-07-22',
        'wife_name' => 'Rina',
        'position' => 'CTO',
        'hobby' => 'Gaming'
    ],
    [
        'id' => 3,
        'first_name' => 'Dos',
        'last_name' => 'Byte',
        'nickname' => '2byte',
        'birthdate' => '1997-07-22',
        'wife_name' => 'Waguri',
        'position' => 'Administrator',
        'hobby' => 'Gym'
    ],
    [
        'id' => 4,
        'first_name' => 'Rudi',
        'last_name' => 'Hartono',
        'nickname' => 'Rud',
        'birthdate' => '1992-01-30',
        'wife_name' => 'Lina',
        'position' => 'Senior Developer',
        'hobby' => 'Reading'
    ],
    [
        'id' => 5,
        'first_name' => 'Sari',
        'last_name' => 'Kusuma',
        'nickname' => 'Sar',
        'birthdate' => '1995-05-18',
        'wife_name' => '',
        'position' => 'UI/UX Designer',
        'hobby' => 'Drawing'
    ],
    [
        'id' => 6,
        'first_name' => 'Joko',
        'last_name' => 'Prasetyo',
        'nickname' => 'Jok',
        'birthdate' => '1987-09-12',
        'wife_name' => 'Maya',
        'position' => 'DevOps Engineer',
        'hobby' => 'Fishing'
    ]
];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Our Team - TechCorp Indonesia</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <div class="page-header">
        <div class="container">
            <h1>Meet Our Team</h1>
            <p>Passionate professionals dedicated to your success</p>
        </div>
    </div>

    <section class="team-section">
        <div class="container">
            <div class="employees-grid">
                <?php foreach ($employees as $emp): ?>
                    <a href="profile.php?id=<?php echo $emp['id']; ?>" class="employee-card">
                        <div class="employee-avatar">
                            <img src="https://ui-avatars.com/api/?name=<?php echo urlencode($emp['first_name'] . '+' . $emp['last_name']); ?>&size=200&background=667eea&color=fff" 
                                 alt="<?php echo htmlspecialchars($emp['first_name'] . ' ' . $emp['last_name']); ?>">
                        </div>
                        <h3 class="employee-name"><?php echo htmlspecialchars($emp['first_name'] . ' ' . $emp['last_name']); ?></h3>
                        <p class="employee-position"><?php echo htmlspecialchars($emp['position']); ?></p>
                        <p class="employee-nickname">"<?php echo htmlspecialchars($emp['nickname']); ?>"</p>
                    </a>
                <?php endforeach; ?>
            </div>
        </div>
    </section>

    <?php include 'includes/footer.php'; ?>
</body>
</html>
