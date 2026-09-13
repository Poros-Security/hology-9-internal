<?php

namespace App\Model;

use PDO;

class OwnerNote
{
    private $db;

    public function __construct(PDO $db)
    {
        $this->db = $db;
    }

    public function all()
    {
        return $this->db->query('SELECT title, body, created_at FROM owner_notes ORDER BY created_at DESC, id DESC')->fetchAll();
    }
}
