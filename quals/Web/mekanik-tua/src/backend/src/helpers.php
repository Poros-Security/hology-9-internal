<?php

use Psr\Http\Message\ResponseInterface;

function json(ResponseInterface $response, $status, array $body)
{
    $response->getBody()->write(json_encode($body));

    return $response->withStatus($status);
}
