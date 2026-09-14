<?php

namespace App\Controller;

use App\Model\Job;
use App\Model\Vehicle;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class JobsController extends Controller
{
    private $jobs;
    private $vehicles;

    public function __construct(Job $jobs, Vehicle $vehicles)
    {
        $this->jobs = $jobs;
        $this->vehicles = $vehicles;
    }

    public function list(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        return json($response, 200, ['jobs' => $this->jobs->forUser($userId)]);
    }

    public function get(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        $id = (int) ($request->getQueryParams()['id'] ?? 0);
        $job = $this->jobs->findForUser($id, $userId);

        if (!$job) {
            return json($response, 404, ['error' => 'not found']);
        }

        return json($response, 200, ['job' => $job, 'notes' => $this->jobs->notes($id)]);
    }

    public function create(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        $input = $this->input($request);
        $complaint = trim($input['complaint'] ?? '');
        $vehicleId = (int) ($input['vehicle_id'] ?? 0);

        if ($complaint === '') {
            return json($response, 400, ['error' => 'complaint is required']);
        }

        if (!$this->vehicles->findForUser($vehicleId, $userId)) {
            return json($response, 404, ['error' => 'not found']);
        }

        return json($response, 200, ['ok' => true, 'id' => $this->jobs->create($userId, $vehicleId, $complaint)]);
    }

    public function vehicles(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        return json($response, 200, ['vehicles' => $this->vehicles->forUser($userId)]);
    }

    public function addVehicle(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        $input = $this->input($request);
        $plate = strtoupper(trim($input['plate'] ?? ''));
        $model = trim($input['model'] ?? '');
        $year = (int) ($input['year'] ?? 0);

        if (!preg_match('/^[A-Z]{1,2} ?[0-9]{1,4} ?[A-Z]{0,3}$/', $plate)) {
            return json($response, 400, ['error' => 'invalid plate']);
        }

        if ($model === '' || $year < 1970 || $year > (int) date('Y')) {
            return json($response, 400, ['error' => 'invalid vehicle']);
        }

        return json($response, 200, ['ok' => true, 'id' => $this->vehicles->create($userId, $plate, $model, $year)]);
    }
}
