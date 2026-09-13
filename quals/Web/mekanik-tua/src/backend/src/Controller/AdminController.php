<?php

namespace App\Controller;

use App\Model\Job;
use App\Model\OwnerNote;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class AdminController extends Controller
{
    private $jobs;
    private $ownerNotes;

    public function __construct(Job $jobs, OwnerNote $ownerNotes)
    {
        $this->jobs = $jobs;
        $this->ownerNotes = $ownerNotes;
    }

    public function overview(Request $request, Response $response)
    {
        if ($this->role() !== 'staff') {
            return json($response, 403, ['error' => 'staff only', 'seen_role' => $this->role()]);
        }

        return json($response, 200, [
            'jobs' => $this->jobs->all(),
            'owner_notes' => $this->ownerNotes->all(),
        ]);
    }
}
