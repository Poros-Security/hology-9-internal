FROM php:8.2-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libicu-dev \
    libzip-dev \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-install intl zip mysqli pdo pdo_mysql

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Apache config — serve from /var/www/html/public
ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' \
    /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' \
    /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Allow .htaccess override
RUN sed -i '/<Directory \/var\/www\/>/,/<\/Directory>/ s/AllowOverride None/AllowOverride All/' \
    /etc/apache2/apache2.conf

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Install CodeIgniter 4.7.3 (VULNERABLE — fixed in 4.7.4)
RUN composer config -g process-timeout 1800 \
    && for i in 1 2 3 4 5; do \
        if composer create-project codeigniter4/appstarter:4.7.3 . --no-interaction --no-dev \
            && composer require codeigniter4/framework:4.7.3 --no-interaction; then \
            break; \
        fi; \
        rm -rf ./* ./.gitignore ./.htaccess 2>/dev/null; \
        echo "composer retry $i"; \
    done

# Configure for development
RUN cp env .env \
    && sed -i 's/# CI_ENVIRONMENT = production/CI_ENVIRONMENT = development/' .env

# Create writable uploads directory
RUN mkdir -p public/uploads && chmod 777 public/uploads writable

# Copy the app over the scaffold
COPY --chown=www-data:www-data app/Controllers/Upload.php app/Controllers/
COPY --chown=www-data:www-data app/Config/Routes.php app/Config/
COPY --chown=www-data:www-data app/Views/index.php app/Views/
COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && chmod -R 777 public/uploads writable

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]
