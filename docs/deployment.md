# Telepítés és üzemeltetés

Éles és staging környezet beüzemelése VPS-en: szerver előkészítés, SSH, DNS, SSL, CI/CD, staging, cron job-ok, mentések, monitoring, secret kezelés.

## 1. Éles telepítés

### Automatizált telepítés (ajánlott)

```bash
ssh root@your-vps-ip
curl -fsSL https://raw.githubusercontent.com/ghemrich/openschool-platform/main/scripts/bootstrap-vps.sh -o bootstrap-vps.sh
bash bootstrap-vps.sh
```

A szkript interaktívan kérdezi a domain-t és GitHub OAuth adatokat, majd automatikusan:
- Telepíti a Dockert + tűzfalat (UFW: 22, 80, 443)
- Létrehozza az `openschool` deploy usert és a `/opt/openschool` könyvtárat
- Klónozza a repót, erős jelszavakkal generálja a `.env.prod`-ot
- Elindítja a szolgáltatásokat, futtatja a migrációkat
- Beállítja a Let's Encrypt SSL-t és a karbantartási cron job-okat (`provision.sh`)

Bootstrap után futtasd: `./scripts/security-check.sh`

### Manuális telepítés

#### Szerver előkészítése

```bash
ssh root@your-vps-ip

# Rendszerfrissítés + Docker
apt-get update && apt-get install -y curl git ufw
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin

# Tűzfal — csak SSH, HTTP, HTTPS
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

# Deploy felhasználó (nem root, nem kell sudo)
useradd -m -s /bin/bash openschool
usermod -aG docker openschool
mkdir -p /opt/openschool && chown openschool:openschool /opt/openschool
```

#### Klónozás és konfig

```bash
su - openschool
cd /opt/openschool
git clone git@github.com:ghemrich/openschool-platform.git .

# .env.prod generálása
DB_PASS=$(openssl rand -base64 24)
SECRET=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 20)

cat > .env.prod << EOF
DB_USER=openschool
DB_PASSWORD=$DB_PASS
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:${DB_PASS}@db:5432/openschool
SECRET_KEY=$SECRET
BASE_URL=https://yourdomain.com
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
GITHUB_CLIENT_ID=production_client_id
GITHUB_CLIENT_SECRET=production_client_secret
GITHUB_WEBHOOK_SECRET=$WEBHOOK_SECRET
PROD_DOMAIN=yourdomain.com
STAGING_DOMAIN=staging.yourdomain.com
EOF

chmod 600 .env.prod
ln -sf .env.prod .env
```

#### Indítás

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head
curl http://localhost/health
```

## 2. SSH biztonság

```bash
# Kulcs generálása (helyi gépről)
ssh-keygen -t ed25519 -C "your_email@example.com"
ssh-copy-id root@VPS_IP

# Jelszavas bejelentkezés letiltása (VPS-en)
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```

> Ne zárd be az SSH munkamenetet, amíg nem ellenőrizted másik terminálból, hogy a kulcs alapú belépés működik!

## 3. DNS és Cloudflare

| Típus | Név | Érték | Proxy |
|-------|-----|-------|-------|
| A | `@` | `VPS_IP` | Proxied |

**SSL/TLS mód:** Full (Strict) — érvényes Let's Encrypt cert kell a VPS-en.

| Mód | Cloudflare → Origin | Biztonság |
|-----|---------------------|----------|
| Flexible | HTTP | ⚠️ Félig titkosított |
| Full | HTTPS (self-signed is) | ✅ |
| **Full (Strict)** | **HTTPS (érvényes cert)** | **✅ Ajánlott** |

## 4. SSL/TLS (Let's Encrypt)

### Standalone mód

```bash
apt-get install certbot
docker compose -f docker-compose.prod.yml stop nginx   # 80-as port felszabadítása
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Nginx SSL konfig frissítése:

```nginx
server {
    listen 80;
    location /health { proxy_pass http://backend/health; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

Tanúsítványok csatolása a `docker-compose.prod.yml`-ben:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

### Cloudflare DNS-01 (proxy maradhat bekapcsolva)

```bash
apt-get install python3-certbot-dns-cloudflare

cat > /etc/letsencrypt/cloudflare.ini << EOF
dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN
EOF
chmod 600 /etc/letsencrypt/cloudflare.ini

certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d yourdomain.com
```

### Automatikus megújítás

```bash
certbot renew --dry-run   # teszt
echo "0 3 * * * certbot renew --quiet && docker compose -f /opt/openschool/docker-compose.prod.yml restart nginx" | sudo tee /etc/cron.d/certbot-renew
```

## 5. CI/CD Pipeline

### CI (minden push és PR)

4 párhuzamos job: backend lint (`ruff`), frontend lint (ESLint + Prettier + `tsc`), backend test (`pytest`), frontend test (Vitest + build).

### CD (main branch push, ha tesztek zöldek)

1. SSH kapcsolat a VPS-hez
2. `git pull origin main`
3. Docker konténerek újraépítése
4. Alembic migrációk
5. Health check

### Deploy SSH kulcs

```bash
# VPS-en, deploy felhasználóként
ssh-keygen -t ed25519 -C "deploy@openschool" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
cat ~/.ssh/id_ed25519  # → ezt másold a GitHub Secrets-be
```

### GitHub beállítások

| Típus | Név | Érték |
|-------|-----|-------|
| Variable | `VPS_HOST` | VPS IP-cím |
| Secret | `VPS_USER` | `openschool` |
| Secret | `VPS_SSH_KEY` | Privát SSH kulcs |

Ha `VPS_HOST` nincs beállítva, a deploy lépés kihagyásra kerül.

## 6. Staging környezet

A staging a production mellett fut ugyanazon a VPS-en. Teljesen elkülönített: saját DB, saját OAuth app, saját domain.

### Architektúra

```
Internet → Cloudflare → Production nginx
  ├── yourdomain.com → backend (prod)
  └── staging.yourdomain.com → openschool-net → Staging nginx → backend (staging)
```

A production nginx terminálja az SSL-t mindkét domainhez; a staging nginx HTTP-only.

### Beállítás lépésről lépésre

**1. Külön GitHub OAuth app** — callback: `https://staging.yourdomain.com/api/auth/callback`

**2. Docker hálózat:**
```bash
docker network create openschool-net
```

**3. Staging könyvtár:**
```bash
mkdir -p /opt/openschool-staging && chown openschool:openschool /opt/openschool-staging
su - openschool && cd /opt/openschool-staging
git clone -b develop git@github.com:ghemrich/openschool-platform.git .
```

**4. `.env.staging` fájl** (ugyanaz a struktúra, mint `.env.prod`, de `ENVIRONMENT=staging`, külön DB/OAuth/domain):
```bash
cat > .env.staging << EOF
DB_USER=openschool_staging
DB_PASSWORD=$(openssl rand -base64 24)
DB_NAME=openschool_staging
DATABASE_URL=postgresql://openschool_staging:...@db:5432/openschool_staging
SECRET_KEY=$(openssl rand -hex 32)
BASE_URL=https://staging.yourdomain.com
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
GITHUB_CLIENT_ID=staging_client_id
GITHUB_CLIENT_SECRET=staging_client_secret
EOF
chmod 600 .env.staging && ln -sf .env.staging .env
```

**5. Production konfig frissítése** — nginx az `openschool-net` hálózaton proxy-zza a staging-et. A `docker-compose.prod.yml`-ben:
```yaml
nginx:
  networks: [default, openschool-net]
networks:
  openschool-net:
    external: true
```

Az `nginx/nginx.conf.template` `envsubst`-tel kapja a `PROD_DOMAIN` és `STAGING_DOMAIN` változókat.

**6. Staging DNS:** `staging.yourdomain.com → A → VPS_IP`

**7. Staging SSL:** külön Let's Encrypt cert a staging domainhez.

**8. Indítás:**
```bash
cd /opt/openschool-staging
docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head
```

### Staging vs Production

| Szempont | Staging | Production |
|----------|---------|------------|
| Branch | `develop` | `main` |
| Domain | `staging.yourdomain.com` | `yourdomain.com` |
| Compose fájl | `docker-compose.staging.yml` | `docker-compose.prod.yml` |
| Swagger UI | Elérhető | Letiltva |
| SSL | Production nginx terminálja | Közvetlen Let's Encrypt |
| Deploy | Manuális / develop push | Automatikus main push |

## 7. Cron job-ok és monitoring

### Ütemezés

| Ütemezés | Feladat | Parancs |
|----------|---------|---------|
| Naponta 02:00 | DB mentés, health check, log hibakeresés | `maintenance.sh full-daily` |
| Hetente V 03:00 | + lemezhasználat, Docker cleanup, DB statisztikák | `maintenance.sh full-weekly` |
| Havonta 1-jén 04:00 | + SSL ellenőrzés, pip-audit | `maintenance.sh full-monthly` |

### Telepítés

```bash
# Automatikus — provision.sh mindent beállít (első alkalommal)
sudo ./scripts/provision.sh

# Vagy csak a cron job-ok
sudo ./scripts/setup-cron.sh
```

A CD pipeline a deploy végén automatikusan frissíti a cron job-okat.

### Karbantartási parancsok

```bash
./scripts/maintenance.sh health          # konténer + /health + DB
./scripts/maintenance.sh backup          # gzip-elt dump, régi mentések törlése
./scripts/maintenance.sh disk            # fájlrendszer + Docker + mentések mérete
./scripts/maintenance.sh docker-cleanup  # régi image-ek, build cache (>30 nap)
./scripts/maintenance.sh ssl-check       # tanúsítvány lejárat
./scripts/maintenance.sh security-audit  # pip-audit
./scripts/maintenance.sh log-errors      # utolsó 500 sor hibakeresés
./scripts/maintenance.sh db-status       # kapcsolatok, tábla méretek, migráció verzió
```

### Karbantartási konfig

```bash
# /etc/openschool-maintenance.conf
BACKUP_DIR=/opt/openschool/backups
BACKUP_RETENTION_DAYS=30
SSL_DOMAIN=yourdomain.com
SSL_WARNING_DAYS=30
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
LOG_FILE=/var/log/openschool-maintenance.log
```

### Discord monitoring értesítések

A `maintenance.sh` Discord webhook-on értesít hibáknál:

| Esemény | Értesítés |
|---------|-----------|
| Mentés sikertelen | DB nem elérhető, backup hiba |
| Health check hiba | Konténer leállt, /health nem válaszol |
| Lemezhasználat ≥90% | Kritikus figyelmeztetés |
| SSL lejár ≤30 napon belül | Tanúsítvány lejárati figyelmeztetés |

Webhook beállítása: Discord szerver → csatorna → Integrációk → Webhookok → URL másolása → `/etc/openschool-maintenance.conf`-ba írása.

## 8. Mentések

### Lokális mentés

```bash
./scripts/maintenance.sh backup   # gzip-elt pg_dump, BACKUP_RETENTION_DAYS napig őrzi
```

### Távoli mentés (ajánlott)

```bash
# rsync másik szerverre (cron-ból naponta)
0 5 * * * youruser rsync -az /opt/openschool/backups/ backup-server:/backups/openschool/

# Vagy S3-kompatibilis tároló
0 5 * * * youruser aws s3 sync /opt/openschool/backups/ s3://your-bucket/openschool-backups/ --delete
```

### Visszaállítás

```bash
gunzip -c /opt/openschool/backups/db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U openschool -d openschool
```

## 9. Secret kezelés

### Erős secret-ek generálása

```bash
openssl rand -hex 32      # SECRET_KEY
openssl rand -base64 24   # DB jelszó
openssl rand -hex 20      # Webhook secret
```

### `pass` (GPG-alapú jelszókezelő)

```bash
apt install -y pass gnupg
gpg --full-generate-key
pass init "GPG_KEY_ID"

# Titkos kulcsok tárolása
pass insert openschool/db-password
pass insert openschool/secret-key
pass generate openschool/secret-key 32

# .env.prod generálása pass-ból
cat > .env.prod << EOF
DB_PASSWORD=$(pass openschool/db-password)
SECRET_KEY=$(pass openschool/secret-key)
...
EOF
```

### Secret rotáció

| Titok | Rotáció | Parancs |
|-------|---------|---------|
| `SECRET_KEY` | Negyedévente | `openssl rand -hex 32` |
| DB jelszó | Negyedévente | `openssl rand -base64 24` |
| GitHub OAuth | Évente | GitHub Developer Settings |
| SSH kulcsok | Évente | `ssh-keygen -t ed25519` |

## 10. Biztonsági ellenőrzőlista

```bash
./scripts/security-check.sh   # automatikus ellenőrzés
```

| Elem | Elvárt |
|------|--------|
| `SECRET_KEY` | Egyedi, ≥32 karakter |
| `ENVIRONMENT` | `production` (Swagger UI letiltva) |
| `ALLOWED_ORIGINS` | Csak az éles domain |
| HTTPS | Let's Encrypt + HTTP→HTTPS redirect |
| Tűzfal | Csak 80/443, PostgreSQL 5432 nem elérhető kívülről |
| SSH | Kulcs alapú, jelszó letiltva |
| `.env.prod` | `chmod 600` |
| Backup | Napi `pg_dump` cron |
| Cloudflare SSL | Full (Strict) |

## 11. Hibaelhárítás

| Probléma | Megoldás |
|----------|----------|
| Docker jogosultsági hiba | `usermod -aG docker $USER`, újra belépés |
| 80-as port foglalt | `lsof -i :80`, másik szolgáltatás leállítása |
| DB connection error | `docker compose ps db`, `docker compose logs db` |
| Frontend változás nem látszik | `docker compose up --build frontend && docker compose restart nginx` |
| OAuth callback hiba | Ellenőrizd a Client ID/Secret-et és a callback URL-t |
| Alembic `DuplicateTable` | `alembic stamp head` (szinkronba hozza a verziót) |
| SSH host key hiba (VPS újratelepítés) | `ssh-keygen -R VPS_IP` |
| Cloudflare 522 | Konténerek futnak? Port 443 nyitva? SSL mód Full (Strict)? |
| Cron nem fut | `systemctl status cron` → `systemctl start cron` |
| Mentés sikertelen | `DB_USER`/`DB_NAME` ellenőrzése `.env.prod`-ban |
