<?php

use App\Controller\AdminController;
use App\Controller\AuthController;
use App\Controller\DiagnosticsController;
use App\Controller\JobsController;
use App\Controller\UsersController;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

$c = $app->getContainer();

$app->any('/', function (Request $request, Response $response) use ($c) {
    $action = $request->getQueryParams()['action'] ?? '';

    switch ($action) {
        case 'list':
            return $c->get(JobsController::class)->list($request, $response);
        case 'get':
            return $c->get(JobsController::class)->get($request, $response);
        case 'create':
            return $c->get(JobsController::class)->create($request, $response);
        case 'vehicles':
            return $c->get(JobsController::class)->vehicles($request, $response);
        case 'addVehicle':
            return $c->get(JobsController::class)->addVehicle($request, $response);
        case 'register':
            return $c->get(AuthController::class)->register($request, $response);
        case 'login':
            return $c->get(AuthController::class)->login($request, $response);
        case 'changePassword':
            return $c->get(AuthController::class)->changePassword($request, $response);
        case 'me':
            return $c->get(UsersController::class)->me($request, $response);
        case 'updateProfile':
            return $c->get(UsersController::class)->updateProfile($request, $response);
        case 'users':
            return $c->get(UsersController::class)->users($request, $response);
        case 'health':
            return $c->get(DiagnosticsController::class)->health($request, $response);
        case 'version':
            return $c->get(DiagnosticsController::class)->version($request, $response);
        case 'config':
            return $c->get(DiagnosticsController::class)->config($request, $response);
        case 'admin':
            return $c->get(AdminController::class)->overview($request, $response);
        default:
            return json($response, 404, ['error' => 'unknown action']);
    }
});
