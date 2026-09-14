<?php

namespace App\Model;

use PDO;

class Job
{
    private $db;

    public function __construct(PDO $db)
    {
        $this->db = $db;
    }

    public function forUser($userId)
    {
        $stmt = $this->db->prepare(
            'SELECT j.id, j.complaint, j.status, j.created_at, j.updated_at, v.plate, v.model
             FROM jobs j JOIN vehicles v ON v.id = j.vehicle_id
             WHERE j.user_id = ? ORDER BY j.created_at DESC, j.id DESC'
        );
        $stmt->execute([$userId]);

        return $stmt->fetchAll();
    }

    public function findForUser($id, $userId)
    {
        $stmt = $this->db->prepare(
            'SELECT j.id, j.complaint, j.status, j.created_at, j.updated_at, v.plate, v.model, v.year
             FROM jobs j JOIN vehicles v ON v.id = j.vehicle_id
             WHERE j.id = ? AND j.user_id = ?'
        );
        $stmt->execute([$id, $userId]);

        return $stmt->fetch() ?: null;
    }

    public function notes($jobId)
    {
        $stmt = $this->db->prepare(
            'SELECT author, body, created_at FROM job_notes WHERE job_id = ? ORDER BY created_at, id'
        );
        $stmt->execute([$jobId]);

        return $stmt->fetchAll();
    }

    public function create($userId, $vehicleId, $complaint)
    {
        $stmt = $this->db->prepare(
            'INSERT INTO jobs (user_id, vehicle_id, complaint, status) VALUES (?, ?, ?, ?)'
        );
        $stmt->execute([$userId, $vehicleId, $complaint, 'antri']);

        return (int) $this->db->lastInsertId();
    }

    public function all()
    {
        return $this->db->query(
            'SELECT j.id, j.complaint, j.status, j.created_at, j.updated_at, u.username, v.plate, v.model
             FROM jobs j
             JOIN users u ON u.id = j.user_id
             JOIN vehicles v ON v.id = j.vehicle_id
             ORDER BY j.created_at DESC, j.id DESC'
        )->fetchAll();
    }
}
