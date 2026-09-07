<?php
class SimpleDB {
    private $conn;
    
    public function __construct() {
        $driver = getenv('DB_DRIVER') ?: (getenv('DB_HOST') ? 'mysql' : 'sqlite');

        if ($driver === 'sqlite') {
            $this->connectSqlite();
            return;
        }

        $this->connectMysql();
    }

    private function connectMysql() {
        $host = getenv('DB_HOST') ?: 'db';
        $dbname = getenv('DB_NAME') ?: 'codex25DB';
        $username = getenv('DB_USER') ?: 'root';
        $password = getenv('DB_PASS') ?: '';
        
        try {
            $this->conn = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch(PDOException $e) {
            die("Connection failed: " . $e->getMessage());
        }
    }

    private function connectSqlite() {
        $dbPath = getenv('DB_PATH') ?: '/var/www/data/techcorp.sqlite';
        $dbDir = dirname($dbPath);

        if (!is_dir($dbDir)) {
            mkdir($dbDir, 0755, true);
        }

        try {
            $this->conn = new PDO("sqlite:$dbPath");
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $this->conn->exec('PRAGMA foreign_keys = ON');
            $this->initializeSqliteSchema();
        } catch(PDOException $e) {
            die("Connection failed: " . $e->getMessage());
        }
    }

    private function initializeSqliteSchema() {
        $this->conn->exec("
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role TEXT NOT NULL DEFAULT 'guest' CHECK(role IN ('guest', 'admin')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service VARCHAR(100) NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ");
    }
    
    public function userExists($username) {
        $stmt = $this->conn->prepare("SELECT id FROM users WHERE username = ?");
        $stmt->execute([$username]);
        return $stmt->fetch() !== false;
    }
    
    public function createUser($username, $password) {
        try {
            $stmt = $this->conn->prepare("INSERT INTO users (username, password, role) VALUES (?, ?, 'guest')");
            $stmt->execute([$username, password_hash($password, PASSWORD_BCRYPT)]);
            
            $userId = $this->conn->lastInsertId();
            return $this->getUserById($userId);
        } catch(PDOException $e) {
            return false;
        }
    }
    
    public function verifyUser($username, $password) {
        $stmt = $this->conn->prepare("SELECT * FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($user && password_verify($password, $user['password'])) {
            return $user;
        }
        
        return false;
    }
    
    public function getUserById($id) {
        $stmt = $this->conn->prepare("SELECT * FROM users WHERE id = ?");
        $stmt->execute([$id]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
    
    public function createAppointment($userId, $service, $date, $time, $notes = '') {
        try {
            $stmt = $this->conn->prepare(
                "INSERT INTO appointments (user_id, service, appointment_date, appointment_time, notes) 
                 VALUES (?, ?, ?, ?, ?)"
            );
            $stmt->execute([$userId, $service, $date, $time, $notes]);
            return true;
        } catch(PDOException $e) {
            return false;
        }
    }
    
    public function getUserAppointments($userId) {
        $stmt = $this->conn->prepare(
            "SELECT * FROM appointments WHERE user_id = ? ORDER BY appointment_date DESC, appointment_time DESC"
        );
        $stmt->execute([$userId]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}
?>
