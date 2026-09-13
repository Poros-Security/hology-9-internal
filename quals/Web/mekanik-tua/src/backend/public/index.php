<?php

use Pimple\Container;
use Pimple\Psr11\Container as Psr11Container;
use Slim\Factory\AppFactory;

require __DIR__ . '/../vendor/autoload.php';

$container = new Container();
$container['settings'] = require __DIR__ . '/../app/settings.php';

require __DIR__ . '/../app/dependencies.php';

$app = AppFactory::create(null, new Psr11Container($container));

require __DIR__ . '/../app/middleware.php';
require __DIR__ . '/../app/routes.php';

$app->run();
