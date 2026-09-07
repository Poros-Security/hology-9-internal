<?php
session_start();

$employees = [
    1 => [
        'id' => 1,
        'first_name' => 'Budi',
        'last_name' => 'Santoso',
        'nickname' => 'Bud',
        'birthdate' => '1985-03-15',
        'wife_name' => 'Siti',
        'position' => 'CEO & Founder',
        'hobby' => 'Photography',
        'email' => 'budi.santoso@techcorp.id',
        'phone' => '+62 812 3456 7890'
    ],
    2 => [
        'id' => 2,
        'first_name' => 'Andi',
        'last_name' => 'Wijaya',
        'nickname' => 'Andy',
        'birthdate' => '1990-07-22',
        'wife_name' => 'Rina',
        'position' => 'CTO',
        'hobby' => 'Gaming',
        'email' => 'andi.wijaya@techcorp.id',
        'phone' => '+62 813 4567 8901'
    ],
    3 => [
        'id' => 3,
        'first_name' => 'Dos',
        'last_name' => 'Byte',
        'nickname' => '2byte',
        'birthdate' => '1997-07-22',
        'wife_name' => 'Waguri',
        'position' => 'Administrator',
        'hobby' => 'Gym',
        'email' => 'dos.byte@techcorp.id',
        'phone' => '+62 814 5678 9012'
    ],
    4 => [
        'id' => 4,
        'first_name' => 'Rudi',
        'last_name' => 'Hartono',
        'nickname' => 'Rud',
        'birthdate' => '1992-01-30',
        'wife_name' => 'Lina',
        'position' => 'Senior Developer',
        'hobby' => 'Reading',
        'email' => 'rudi.hartono@techcorp.id',
        'phone' => '+62 815 6789 0123'
    ],
    5 => [
        'id' => 5,
        'first_name' => 'Sari',
        'last_name' => 'Kusuma',
        'nickname' => 'Sar',
        'birthdate' => '1995-05-18',
        'wife_name' => '',
        'position' => 'UI/UX Designer',
        'hobby' => 'Drawing',
        'email' => 'sari.kusuma@techcorp.id',
        'phone' => '+62 816 7890 1234'
    ],
    6 => [
        'id' => 6,
        'first_name' => 'Joko',
        'last_name' => 'Prasetyo',
        'nickname' => 'Jok',
        'birthdate' => '1987-09-12',
        'wife_name' => 'Maya',
        'position' => 'DevOps Engineer',
        'hobby' => 'Fishing',
        'email' => 'joko.prasetyo@techcorp.id',
        'phone' => '+62 817 8901 2345'
    ]
];

$id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

if (!isset($employees[$id])) {
    header('Location: team.php');
    exit;
}

$employee = $employees[$id];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo htmlspecialchars($employee['first_name'] . ' ' . $employee['last_name']); ?> - TechCorp Indonesia</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <section class="profile-section">
        <div class="container">
            <div class="profile-content">
                <div class="profile-sidebar">
                    <div class="profile-avatar-large">
                        <img src="https://ui-avatars.com/api/?name=<?php echo urlencode($employee['first_name'] . '+' . $employee['last_name']); ?>&size=400&background=667eea&color=fff" 
                             alt="<?php echo htmlspecialchars($employee['first_name'] . ' ' . $employee['last_name']); ?>">
                    </div>
                </div>

                <div class="profile-main">
                    <div class="profile-title">
                        <h1><?php echo htmlspecialchars($employee['first_name'] . ' ' . $employee['last_name']); ?></h1>
                        <p class="profile-nickname">Nickname: "<?php echo htmlspecialchars($employee['nickname']); ?>"</p>
                        <p class="profile-position"><?php echo htmlspecialchars($employee['position']); ?></p>
                    </div>

                    <div class="profile-section-box">
                        <h2>Personal Information</h2>
                        <div class="profile-info-grid">
                            <div class="profile-info-item">
                                <label>First Name</label>
                                <p><?php echo htmlspecialchars($employee['first_name']); ?></p>
                            </div>
                            <div class="profile-info-item">
                                <label>Last Name</label>
                                <p><?php echo htmlspecialchars($employee['last_name']); ?></p>
                            </div>
                            <div class="profile-info-item">
                                <label>Nickname</label>
                                <p><?php echo htmlspecialchars($employee['nickname']); ?></p>
                            </div>
                            <div class="profile-info-item">
                                <label>Date of Birth</label>
                                <p><?php echo htmlspecialchars(date('d F Y', strtotime($employee['birthdate']))); ?></p>
                            </div>
                            <?php if (!empty($employee['wife_name'])): ?>
                            <div class="profile-info-item">
                                <label>Partner Name</label>
                                <p><?php echo htmlspecialchars($employee['wife_name']); ?></p>
                            </div>
                            <?php endif; ?>
                            <div class="profile-info-item">
                                <label>Hobby</label>
                                <p><?php echo htmlspecialchars($employee['hobby']); ?></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <?php include 'includes/footer.php'; ?>
</body>
</html>
