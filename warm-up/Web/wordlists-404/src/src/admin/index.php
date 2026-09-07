<?php
header('Content-Type: application/json');

$jwt_secret = getenv('JWT_SECRET');
$flag = getenv('GZCTF_FLAG') ?: getenv('FLAG');

if (empty($jwt_secret)) {
    $jwt_secret = 'by73W49ur1$';
}

if (empty($flag)) {
    $flag = 'HOLOGY9{wH3n_yh?_mY_M1n3_Ku_7iB4_e6e67e40_local}';
}

if (empty($jwt_secret) || empty($flag)) {
    http_response_code(500);
    echo json_encode(['error' => 'Server configuration error']);
    exit;
}

// Read JWT from cookie (consistent with login flow)
$token = isset($_COOKIE['auth_token']) ? $_COOKIE['auth_token'] : '';

if (empty($token)) {
    http_response_code(401);
    echo json_encode([
        'error' => 'No authentication token provided',
        'hint' => 'You need to be logged in with a valid JWT token'
    ]);
    exit;
}

function base64url_decode($data) {
    return base64_decode(strtr($data, '-_', '+/'));
}

function verify_jwt($token, $secret) {
    $parts = explode('.', $token);
    
    if (count($parts) !== 3) {
        return false;
    }
    
    list($header, $payload, $signature) = $parts;
    
    $valid_signature = hash_hmac('sha256', "$header.$payload", $secret, true);
    $valid_signature = rtrim(strtr(base64_encode($valid_signature), '+/', '-_'), '=');
    
    return hash_equals($signature, $valid_signature);
}

function decode_jwt_payload($token) {
    $parts = explode('.', $token);
    if (count($parts) !== 3) {
        return null;
    }
    
    $payload = json_decode(base64url_decode($parts[1]), true);
    return $payload;
}

if (!verify_jwt($token, $jwt_secret)) {
    http_response_code(403);
    echo json_encode([
        'error' => 'Invalid or expired token',
        'hint' => 'The JWT signature is invalid. Did you crack the secret?'
    ]);
    exit;
}

// Decode payload and check role
$payload = decode_jwt_payload($token);

if (!$payload || !isset($payload['role']) || $payload['role'] !== 'admin') {
    http_response_code(403);
    echo json_encode([
        'error' => 'Access denied',
        'message' => 'Only admin users can access this endpoint',
        'your_role' => $payload['role'] ?? 'unknown'
    ]);
    exit;
}

http_response_code(200);
echo json_encode([
    'status' => 'success',
    'message' => 'Access granted to development endpoint',
    'flag' => $flag,
    'note' => 'Congratulations! You successfully cracked the JWT secret and forged an admin token.',
    'user' => $payload['username'] ?? 'unknown'
]);
?>
