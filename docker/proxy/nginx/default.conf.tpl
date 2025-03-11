server {
    listen 80 default_server;
    server_name _;

    return 301 https://${DOMAIN}$request_uri;
}

server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /vol/www/;
    }

    location / {
        return 301 https://${DOMAIN}$request_uri;
    }
}
