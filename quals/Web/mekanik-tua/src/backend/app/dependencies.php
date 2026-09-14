<?php

use App\Controller\AdminController;
use App\Controller\AuthController;
use App\Controller\DiagnosticsController;
use App\Controller\JobsController;
use App\Controller\UsersController;
use App\Model\Job;
use App\Model\OwnerNote;
use App\Model\User;
use App\Model\Vehicle;

$container['db'] = function ($c) {
    $db = new PDO('sqlite:' . $c['settings']['db_path']);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $db->exec('PRAGMA foreign_keys = ON');

    return $db;
};

$container['users'] = function ($c) {
    return new User($c['db']);
};

$container['jobs'] = function ($c) {
    return new Job($c['db']);
};

$container['vehicles'] = function ($c) {
    return new Vehicle($c['db']);
};

$container['ownerNotes'] = function ($c) {
    return new OwnerNote($c['db']);
};

$container[JobsController::class] = function ($c) {
    return new JobsController($c['jobs'], $c['vehicles']);
};

$container[AuthController::class] = function ($c) {
    return new AuthController($c['users'], $c['settings']['app_pepper']);
};

$container[AdminController::class] = function ($c) {
    return new AdminController($c['jobs'], $c['ownerNotes']);
};

$container[DiagnosticsController::class] = function ($c) {
    return new DiagnosticsController($c['settings']);
};

$container[UsersController::class] = function ($c) {
    return new UsersController($c['users']);
};
