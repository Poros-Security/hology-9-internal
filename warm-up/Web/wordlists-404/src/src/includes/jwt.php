<?php
class JWT {
    private static function base64url_encode($data) {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
    
    private static function base64url_decode($data) {
        return base64_decode(strtr($data, '-_', '+/'));
    }
    
    public static function generate($payload, $secret) {
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        $header = self::base64url_encode($header);
        $payload = self::base64url_encode(json_encode($payload));
        
        $signature = hash_hmac('sha256', "$header.$payload", $secret, true);
        $signature = self::base64url_encode($signature);
        
        return "$header.$payload.$signature";
    }
    
    public static function verify($token, $secret) {
        $parts = explode('.', $token);
        
        if (count($parts) !== 3) {
            return false;
        }
        
        list($header, $payload, $signature) = $parts;
        
        $valid_signature = hash_hmac('sha256', "$header.$payload", $secret, true);
        $valid_signature = self::base64url_encode($valid_signature);
        
        return hash_equals($signature, $valid_signature);
    }
    
    public static function decode($token) {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            return null;
        }
        
        $payload = self::base64url_decode($parts[1]);
        return json_decode($payload, true);
    }
}
?>