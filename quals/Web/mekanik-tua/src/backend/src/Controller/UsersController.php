<?php

namespace App\Controller;

use App\Model\User;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class UsersController extends Controller
{
    private $users;

    public function __construct(User $users)
    {
        $this->users = $users;
    }

    public function me(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        return json($response, 200, ['user' => $this->users->profile($userId)]);
    }

    public function updateProfile(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        $phone = trim($this->input($request)['phone'] ?? '');

        if (!preg_match('/^[0-9+][0-9 \-]{5,19}$/u', $phone)) {
            return json($response, 400, ['error' => 'invalid phone']);
        }

        $this->users->setPhone($userId, $phone);

        return json($response, 200, ['ok' => true]);
    }

    public function users(Request $request, Response $response)
    {
        return json($response, 200, ['users' => $this->users->all()]);
    }
}
