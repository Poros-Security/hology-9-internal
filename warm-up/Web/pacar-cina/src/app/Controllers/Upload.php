<?php

namespace App\Controllers;

use CodeIgniter\Controller;

class Upload extends Controller
{
    public function index()
    {
        helper(['form', 'filesystem']);

        if ($this->request->getMethod() === 'POST') {
            $validation = \Config\Services::validation();
            $validation->setRules([
                'avatar' => 'uploaded[avatar]|max_size[avatar,2048]|is_image[avatar]',
            ]);

            if (! $validation->withRequest($this->request)->run()) {
                return view('index', [
                    'error' => implode(', ', $validation->getErrors()),
                ]);
            }

            $file = $this->request->getFile('avatar');
            if (! $file->isValid()) {
                return view('index', [
                    'error' => 'File invalid: ' . $file->getErrorString(),
                ]);
            }

            $clientName = $file->getClientName();
            $mime       = $file->getMimeType();
            $size       = $file->getSize();
            $file->move(FCPATH . 'uploads/', $clientName);

            return view('index', [
                'success' => "Avatar uploaded successfully!",
                'path'    => "/uploads/{$clientName}",
                'mime'    => $mime,
                'size'    => $size,
            ]);
        }

        return view('index');
    }
}
