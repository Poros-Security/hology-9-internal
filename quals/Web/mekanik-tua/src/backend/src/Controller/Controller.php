<?php

namespace App\Controller;

use Psr\Http\Message\ServerRequestInterface as Request;

abstract class Controller
{
    protected function userId()
    {
        return isset($_SESSION['uid']) ? (int) $_SESSION['uid'] : 0;
    }

    protected function role()
    {
        return isset($_SESSION['role']) ? $_SESSION['role'] : null;
    }

    protected function input(Request $request)
    {
        return array_merge((array) $request->getParsedBody(), $request->getQueryParams());
    }
}
