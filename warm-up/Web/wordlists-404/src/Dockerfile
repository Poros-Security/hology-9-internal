FROM php:8.1-apache

RUN a2enmod rewrite && \
    sed -i '/<Directory \/var\/www\/>/,/<\/Directory>/ s/AllowOverride None/AllowOverride All/' /etc/apache2/apache2.conf

WORKDIR /var/www/html

ENV DB_DRIVER=sqlite \
    DB_PATH=/var/www/data/techcorp.sqlite

COPY ./php.ini /usr/local/etc/php/php.ini
COPY ./src /var/www/html/

RUN mkdir -p /var/www/data && \
    chown -R www-data:www-data /var/www/html /var/www/data && \
    chmod -R 755 /var/www/html

EXPOSE 80

CMD ["apache2-foreground"]
