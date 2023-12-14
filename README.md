# finance

The backend system calculates the total balance of accounts 
in different currencies by converting them into a single base currency 
using up-to-date exchange rates.

### Build:
docker compose -f docker-compose-local.yml build

### Start:
docker compose -f docker-compose-local.yml up -d

### Stop:
docker compose -f docker-compose-local.yml down

# certificats

### check domain

dig {$DOMAIN}

### get first cert

docker compose -f docker-compose-stage.yml run --rm certbot /opt/certify-init.sh

### update cert

docker compose -f docker-compose-stage.yml run --rm certbot sh -c "certbot renew"