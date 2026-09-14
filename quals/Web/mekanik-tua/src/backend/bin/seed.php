<?php

use App\Model\User;

require __DIR__ . '/../vendor/autoload.php';

$settings = require __DIR__ . '/../app/settings.php';

$flag = getenv('GZCTF_FLAG');

if (!$flag) {
    fwrite(STDERR, "GZCTF_FLAG is not set\n");
    exit(1);
}

$pepper = $settings['app_pepper'];
$dbPath = $settings['db_path'];

if (!is_dir(dirname($dbPath))) {
    mkdir(dirname($dbPath), 0750, true);
}

$db = new PDO('sqlite:' . $dbPath);
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$db->exec(file_get_contents(__DIR__ . '/../database/schema.sql'));

$staffPassword = 'adm-' . bin2hex(random_bytes(24));

$customers = [
    [
        'username' => 'budi_s',
        'password' => 'budi1234',
        'phone' => '081234567890',
        'joined' => 640,
        'vehicles' => [
            ['N 4521 AB', 'Honda Supra X 125', 2009],
            ['N 6677 CD', 'Yamaha Mio Soul', 2013],
        ],
        'jobs' => [
            [0, 'Rem belakang bunyi, kadang gak pakem', 'selesai', 52, [
                ['Pak Yanto', 'Kampas rem habis, ganti baru. Sekalian setel rantai.', 51],
                ['Pak Yanto', 'Sudah dites keliling, aman. Bisa diambil.', 50],
            ]],
            [1, 'Motor susah distarter pagi hari, aki sudah diganti bulan lalu', 'tunggu-sparepart', 12, [
                ['Agus', 'Kiprok lemah. Pesan ke toko Sumber Jaya, kira2 3 hari.', 11],
            ]],
            [0, 'Servis rutin 10.000 km', 'antri', 3, []],
        ],
    ],
    [
        'username' => 'siti_r',
        'password' => 'sitirahayu',
        'phone' => '085712345678',
        'joined' => 580,
        'vehicles' => [
            ['L 1987 EF', 'Honda Vario 150', 2016],
        ],
        'jobs' => [
            [0, 'Ganti oli + cek CVT, sudah mulai getar', 'dikerjakan', 5, [
                ['Agus', 'Roller aus semua. Ganti satu set sama v-belt.', 4],
            ]],
        ],
    ],
    [
        'username' => 'agus_p',
        'password' => 'aguspurnomo',
        'phone' => '081559874321',
        'joined' => 410,
        'vehicles' => [
            ['N 2210 GH', 'Suzuki Satria FU 150', 2014],
            ['N 8834 JK', 'Honda Beat', 2018],
        ],
        'jobs' => [
            [0, 'Gigi 4 susah masuk', 'selesai', 44, [
                ['Pak Yanto', 'Setelan kopling. Sudah beres, gak perlu bongkar.', 43],
            ]],
            [1, 'Lampu depan mati total', 'selesai', 20, [
                ['Wid', 'Sekring putus, ganti. Cek kabel body sekalian.', 20],
            ]],
        ],
    ],
    [
        'username' => 'dewi_a',
        'password' => 'dewiayu2016',
        'phone' => '087865443321',
        'joined' => 355,
        'vehicles' => [
            ['N 7712 LM', 'Yamaha Jupiter Z1', 2015],
        ],
        'jobs' => [
            [0, 'Suara mesin kasar waktu jalan pelan', 'dikerjakan', 8, [
                ['Agus', 'Klep perlu disetel. Sekalian bersihin karbu.', 7],
            ]],
        ],
    ],
    [
        'username' => 'rizky_h',
        'password' => 'rizkyhakim',
        'phone' => '089612347788',
        'joined' => 260,
        'vehicles' => [
            ['N 3390 NP', 'Honda CB150R', 2017],
        ],
        'jobs' => [
            [0, 'Ban belakang sering kempes, tambal terus bocor lagi', 'selesai', 31, [
                ['Wid', 'Velg peyang dikit. Sudah dipress, ganti ban dalam.', 30],
            ]],
            [0, 'Rantai kendor bunyi', 'antri', 2, []],
        ],
    ],
    [
        'username' => 'yuni_k',
        'password' => 'yunikartika',
        'phone' => '082245567712',
        'joined' => 150,
        'vehicles' => [
            ['N 5508 QR', 'Yamaha NMAX', 2019],
        ],
        'jobs' => [
            [0, 'Servis rutin sama ganti oli gardan', 'tunggu-sparepart', 6, [
                ['Agus', 'Oli gardan kosong, nunggu kiriman Senin.', 5],
            ]],
        ],
    ],
];

$ownerNotes = [
    ['Stok oli', 'Yamalube tinggal 4 botol, pesan lagi hari Senin. Federal masih banyak.', 40],
    ['Pak Yanto cuti', 'Tanggal 17 sampai 20. Agus pegang bengkel, Wid bantu sore.', 22],
    ['Setoran', 'Sisa tagihan Sumber Jaya belum dibayar, catat dulu di buku.', 9],
    ['Catatan sistem', $flag, 4],
];

$insertUser = $db->prepare(
    'INSERT INTO users (username, password_hash, pw_salt, phone, role, created_at)
     VALUES (?, ?, ?, ?, ?, ?)'
);
$insertVehicle = $db->prepare('INSERT INTO vehicles (user_id, plate, model, year) VALUES (?, ?, ?, ?)');
$insertJob = $db->prepare(
    'INSERT INTO jobs (user_id, vehicle_id, complaint, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)'
);
$insertNote = $db->prepare('INSERT INTO job_notes (job_id, author, body, created_at) VALUES (?, ?, ?, ?)');
$insertOwnerNote = $db->prepare('INSERT INTO owner_notes (title, body, created_at) VALUES (?, ?, ?)');

$at = function ($daysAgo) {
    return date('Y-m-d H:i:s', strtotime('-' . $daysAgo . ' days'));
};

$store = function ($username, $password, $phone, $role, $joined) use ($db, $insertUser, $pepper, $at) {
    $salt = User::newSalt();
    $insertUser->execute([$username, User::hash($pepper, $password, $salt), $salt, $phone, $role, $at($joined)]);

    return (int) $db->lastInsertId();
};

$db->beginTransaction();

foreach ($customers as $customer) {
    $userId = $store($customer['username'], $customer['password'], $customer['phone'], 'customer', $customer['joined']);

    $vehicleIds = [];

    foreach ($customer['vehicles'] as $vehicle) {
        $insertVehicle->execute([$userId, $vehicle[0], $vehicle[1], $vehicle[2]]);
        $vehicleIds[] = (int) $db->lastInsertId();
    }

    foreach ($customer['jobs'] as $job) {
        list($vehicleIndex, $complaint, $status, $daysAgo, $notes) = $job;
        $lastTouched = $notes ? end($notes)[2] : $daysAgo;

        $insertJob->execute([$userId, $vehicleIds[$vehicleIndex], $complaint, $status, $at($daysAgo), $at($lastTouched)]);
        $jobId = (int) $db->lastInsertId();

        foreach ($notes as $note) {
            $insertNote->execute([$jobId, $note[0], $note[1], $at($note[2])]);
        }
    }
}

$store('pakwid', $staffPassword, '0341551234', 'staff', 700);

foreach ($ownerNotes as $note) {
    $insertOwnerNote->execute([$note[0], $note[1], $at($note[2])]);
}

$db->commit();

file_put_contents(dirname($dbPath) . '/staff-password.txt', $staffPassword . "\n");
