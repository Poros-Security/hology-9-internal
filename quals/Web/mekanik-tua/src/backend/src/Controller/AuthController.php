<?php

namespace App\Controller;

use App\Model\User;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class AuthController extends Controller
{
    const MIN_PASSWORD = 8;

    private $users;
    private $pepper;

    public function __construct(User $users, $pepper)
    {
        $this->users = $users;
        $this->pepper = $pepper;
    }

    public function register(Request $request, Response $response)
    {
        $input = $this->input($request);
        $username = trim($input['username'] ?? '');
        $password = $input['password'] ?? '';
        $phone = trim($input['phone'] ?? '');

        if (!preg_match('/^[a-z0-9_]{3,20}$/i', $username)) {
            return json($response, 400, ['error' => 'invalid username']);
        }

        if (strlen($password) < self::MIN_PASSWORD) {
            return json($response, 400, ['error' => 'password too short']);
        }

        if ($phone !== '' && !preg_match('/^[0-9+][0-9 \-]{5,19}$/u', $phone)) {
            return json($response, 400, ['error' => 'invalid phone']);
        }

        if ($this->users->findByUsername($username)) {
            return json($response, 409, ['error' => 'username taken']);
        }

        $salt = User::newSalt();
        $id = $this->users->create($username, User::hash($this->pepper, $password, $salt), $salt, $phone);

        return json($response, 200, ['ok' => true, 'id' => $id]);
    }

    public function login(Request $request, Response $response)
    {
        $input = $this->input($request);
        $user = $this->users->findByUsername($input['u'] ?? '');

        if (!$user) {
            return json($response, 401, ['error' => 'bad credentials']);
        }

        $remaining = $this->users->lockRemaining($user);

        if ($remaining > 0) {
            return json($response, 429, ['error' => 'account locked', 'retry_in' => $remaining]);
        }

        if (!User::verify($this->pepper, $input['p'] ?? '', $user['pw_salt'], $user['password_hash'])) {
            $this->users->recordFailure($user);

            return json($response, 401, ['error' => 'bad credentials']);
        }

        $this->users->clearFailures($user['id']);
        session_regenerate_id(true);
        $_SESSION['uid'] = (int) $user['id'];
        $_SESSION['role'] = $user['role'];

        return json($response, 200, ['ok' => true, 'sid' => session_id(), 'role' => $user['role']]);
    }

    public function changePassword(Request $request, Response $response)
    {
        $userId = $this->userId();

        if (!$userId) {
            return json($response, 401, ['error' => 'login required']);
        }

        $input = $this->input($request);
        $user = $this->users->find($userId);

        if (!User::verify($this->pepper, $input['current'] ?? '', $user['pw_salt'], $user['password_hash'])) {
            return json($response, 400, ['error' => 'current password incorrect']);
        }

        $password = $input['password'] ?? '';

        if (strlen($password) < self::MIN_PASSWORD) {
            return json($response, 400, ['error' => 'password too short']);
        }

        $salt = User::newSalt();
        $this->users->setPassword($userId, User::hash($this->pepper, $password, $salt), $salt);

        return json($response, 200, ['ok' => true]);
    }
}
