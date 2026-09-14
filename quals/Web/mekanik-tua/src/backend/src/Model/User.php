<?php

namespace App\Model;

use PDO;

class User
{
    const MAX_ATTEMPTS = 5;
    const LOCK_SECONDS = 300;
    const BCRYPT_COST = 10;

    private $db;

    public function __construct(PDO $db)
    {
        $this->db = $db;
    }

    public static function newSalt()
    {
        return bin2hex(random_bytes(8));
    }

    public static function hash($pepper, $password, $salt)
    {
        return password_hash($pepper . $password . $salt, PASSWORD_BCRYPT, ['cost' => self::BCRYPT_COST]);
    }

    public static function verify($pepper, $password, $salt, $hash)
    {
        return password_verify($pepper . $password . $salt, $hash);
    }

    public function findByUsername($username)
    {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE username = ?');
        $stmt->execute([$username]);

        return $stmt->fetch() ?: null;
    }

    public function find($id)
    {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE id = ?');
        $stmt->execute([$id]);

        return $stmt->fetch() ?: null;
    }

    public function profile($id)
    {
        $stmt = $this->db->prepare('SELECT id, username, phone, role, created_at FROM users WHERE id = ?');
        $stmt->execute([$id]);

        return $stmt->fetch() ?: null;
    }

    public function all()
    {
        return $this->db->query('SELECT id, username, password_hash, pw_salt, role FROM users ORDER BY id')->fetchAll();
    }

    public function create($username, $hash, $salt, $phone)
    {
        $stmt = $this->db->prepare(
            'INSERT INTO users (username, password_hash, pw_salt, phone, role) VALUES (?, ?, ?, ?, ?)'
        );
        $stmt->execute([$username, $hash, $salt, $phone, 'customer']);

        return (int) $this->db->lastInsertId();
    }

    public function setPassword($id, $hash, $salt)
    {
        $stmt = $this->db->prepare('UPDATE users SET password_hash = ?, pw_salt = ? WHERE id = ?');
        $stmt->execute([$hash, $salt, $id]);
    }

    public function setPhone($id, $phone)
    {
        $stmt = $this->db->prepare('UPDATE users SET phone = ? WHERE id = ?');
        $stmt->execute([$phone, $id]);
    }

    public function lockRemaining(array $user)
    {
        return max(0, (int) $user['locked_until'] - time());
    }

    public function recordFailure(array $user)
    {
        $attempts = (int) $user['failed_attempts'] + 1;

        if ($attempts < self::MAX_ATTEMPTS) {
            $stmt = $this->db->prepare('UPDATE users SET failed_attempts = ? WHERE id = ?');
            $stmt->execute([$attempts, $user['id']]);

            return;
        }

        $stmt = $this->db->prepare('UPDATE users SET failed_attempts = 0, locked_until = ? WHERE id = ?');
        $stmt->execute([time() + self::LOCK_SECONDS, $user['id']]);
    }

    public function clearFailures($id)
    {
        $stmt = $this->db->prepare('UPDATE users SET failed_attempts = 0, locked_until = 0 WHERE id = ?');
        $stmt->execute([$id]);
    }
}
