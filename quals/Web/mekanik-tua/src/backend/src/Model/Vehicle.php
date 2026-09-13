<?php

namespace App\Model;

use PDO;

class Vehicle
{
    private $db;

    public function __construct(PDO $db)
    {
        $this->db = $db;
    }

    public function forUser($userId)
    {
        $stmt = $this->db->prepare('SELECT id, plate, model, year FROM vehicles WHERE user_id = ? ORDER BY id');
        $stmt->execute([$userId]);

        return $stmt->fetchAll();
    }

    public function findForUser($id, $userId)
    {
        $stmt = $this->db->prepare('SELECT id, plate, model, year FROM vehicles WHERE id = ? AND user_id = ?');
        $stmt->execute([$id, $userId]);

        return $stmt->fetch() ?: null;
    }

    public function create($userId, $plate, $model, $year)
    {
        $stmt = $this->db->prepare('INSERT INTO vehicles (user_id, plate, model, year) VALUES (?, ?, ?, ?)');
        $stmt->execute([$userId, $plate, $model, $year]);

        return (int) $this->db->lastInsertId();
    }
}
