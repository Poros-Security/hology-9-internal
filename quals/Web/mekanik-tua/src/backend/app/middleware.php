<?php

session_name('api_sid');
session_start();

$app->addBodyParsingMiddleware();

$app->add(function ($request, $handler) {
    return $handler->handle($request)->withHeader('Content-Type', 'application/json; charset=utf-8');
});

$app->addRoutingMiddleware();
$app->addErrorMiddleware(false, true, true);
