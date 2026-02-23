# Production Runbook

## Host hardening

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Deploy

```bash
export DOMAIN=yourdomain.com
./scripts/deploy_prod.sh
```

## Restart / rollback

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f app
```

## Optional systemd startup

```bash
sudo cp deploy/sms-chatbot.service /etc/systemd/system/sms-chatbot.service
sudo systemctl daemon-reload
sudo systemctl enable --now sms-chatbot
```

## Health checks

```bash
curl -sf https://yourdomain.com/api/health
curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com/admin
```

## TLS

TLS certificates are managed automatically by Caddy and stored in the `caddy_data` volume.
