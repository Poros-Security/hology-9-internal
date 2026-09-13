<?php

namespace App\Controller;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class DiagnosticsController extends Controller
{
    private $settings;

    public function __construct(array $settings)
    {
        $this->settings = $settings;
    }

    public function health(Request $request, Response $response)
    {
        return json($response, 200, ['ok' => true]);
    }

    public function version(Request $request, Response $response)
    {
        return json($response, 200, [
            'name' => $this->settings['app_name'],
            'version' => $this->settings['app_version'],
        ]);
    }

    public function config(Request $request, Response $response)
    {
        $fields = $request->getQueryParams()['fields'] ?? '';

        if (preg_match('/pepper|secret|key/iu', $fields)) {
            return json($response, 403, ['error' => 'redacted field requested']);
        }

        $out = [];

        foreach (explode(',', $fields) as $field) {
            if (isset($this->settings[$field])) {
                $out[$field] = $this->settings[$field];
            }
        }

        return json($response, 200, $out);
    }
}
