<?php

$pepper = getenv('APP_PEPPER');

if (strlen($pepper) !== 64) {
    throw new RuntimeException('APP_PEPPER is missing or malformed');
}

return [
    'app_name' => 'mekanik-tua',
    'app_env' => getenv('APP_ENV') ?: 'production',
    'app_version' => '1.4.2',
    'db_path' => getenv('DB_PATH') ?: '/var/lib/mekanik/mt.sqlite',
    'upload_max' => '4M',
    'app_pepper' => $pepper,
];
