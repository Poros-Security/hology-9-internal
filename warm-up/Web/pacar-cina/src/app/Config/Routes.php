<?php

namespace Config;

use CodeIgniter\Router\RouteCollection;

/** @var RouteCollection $routes */

$routes->match(['get', 'post'], '/', 'Upload::index');
