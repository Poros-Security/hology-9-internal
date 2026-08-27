#!/bin/sh

if [ -n "$GZCTF_FLAG" ]; then

    echo "<?php \$SECRET_FLAG = \"$GZCTF_FLAG\"; ?>" > /var/www/html/flag.php
fi

exec "$@"
