# OpenSchool Platform — Telepítési útmutató

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](architektura.md) · **Telepítés** · [Környezeti változók](kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a helyi fejlesztést, a staging és az éles (production) üzembe helyezést ismerteti.

---

## Tartalomjegyzék

1. [Előfeltételek](#előfeltételek)
2. [Helyi fejlesztés (Docker)](#helyi-fejlesztés-docker)
3. [Helyi fejlesztés (Docker nélkül)](#helyi-fejlesztés-docker-nélkül)
4. [Környezeti változók](#környezeti-változók)
5. [Adatbázis és migrációk](#adatbázis-és-migrációk)
6. [GitHub OAuth beállítás](#github-oauth-beállítás)
7. [Tesztek futtatása](#tesztek-futtatása)
8. [Éles telepítés (VPS)](#éles-telepítés-vps)
9. [SSH biztonság](#ssh-biztonság)
10. [DNS és Cloudflare konfiguráció](#dns-és-cloudflare-konfiguráció)
11. [SSL/TLS Let's Encrypt-tel](#ssltls-lets-encrypttel)
12. [Staging telepítés](#staging-telepítés)
13. [Karbantartás és provisioning](#karbantartás-és-provisioning)
14. [Deploy SSH kulcs CI/CD-hez](#deploy-ssh-kulcs-cicd-hez)
15. [Biztonsági mentés](#biztonsági-mentés)
16. [CI/CD Pipeline](#cicd-pipeline)
17. [Hibaelhárítás](#hibaelhárítás)

---

## Előfeltételek

- **Docker** 24+ és **Docker Compose** v2
- **Python** 3.12+ (helyi fejlesztéshez Docker nélkül)
- **Node.js** 20+ (frontend fejlesztéshez)
- **Git**
- **GitHub fiók** (OAuth alkalmazás létrehozásához)

---

## Helyi fejlesztés (Docker)

A leggyorsabb módja a teljes rendszer elindításának:

```bash
# Repó klónozása
git clone git@github.com:ghemrich/openschool-platform.git
cd openschool-platform

# Környezeti fájl létrehozása
cp .env.example .env
# Szerkeszd a .env fájlt a GitHub OAuth adataiddal (lásd "GitHub OAuth beállítás")

# Összes szolgáltatás indítása (backend, db, nginx, frontend)
docker compose up --build -d

# Ellenőrzés
curl http://localhost/health
# → {"status": "ok"}

# Logok megtekintése
docker compose logs -f backend
```

**Futó szolgáltatások:**

| Szolgáltatás | Port | Leírás                      |
|-------------|------|-----------------------------|
| nginx       | 80   | Reverse proxy (belépési pont)|
| backend     | 8000 | FastAPI API (belső)          |
| db          | 5432 | PostgreSQL 16                |
| frontend    | —    | Astro build (statikus fájlok)|

**Hasznos parancsok:**

```bash
make up        # docker compose up --build -d
make down      # docker compose down
make test      # pytest futtatás
make migrate   # alembic migrációk futtatása
make lint      # ruff ellenőrzés + formázás
```

---

## Helyi fejlesztés (Docker nélkül)

Backend fejlesztéshez:

```bash
cd backend

# Virtuális környezet létrehozása
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Függőségek telepítése (produkció)
pip install -r requirements.txt
# Vagy fejlesztéshez (teszt, lint eszközökkel):
# pip install -r requirements-dev.txt

# Környezeti változók beállítása (vagy .env fájl a backend/ könyvtárban)
export DATABASE_URL="postgresql://openschool:openschool@localhost:5432/openschool"
export SECRET_KEY="change-me-in-production"
export BASE_URL="http://localhost"

# Migrációk futtatása
alembic upgrade head

# Szerver indítása
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend fejlesztéshez:

```bash
cd frontend
npm install
npm run dev    # Astro dev szerver: http://localhost:4321
npm run build  # Statikus fájlok buildelése
```

---

## Környezeti változók

Hozz létre egy `.env` fájlt a projekt gyökérkönyvtárában (soha ne commitold):

```bash
# Adatbázis
DB_USER=openschool
DB_PASSWORD=openschool
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:openschool@db:5432/openschool

# Biztonság
SECRET_KEY=change-me-in-production    # JWT aláíró kulcs — élesben random 64 karakteres stringet használj

# Platform
BASE_URL=http://localhost              # Tanúsítványok és QR kódok URL-jéhez
                                       # Élesben: https://yourdomain.com
ENVIRONMENT=development                # development vagy production
ALLOWED_ORIGINS=http://localhost,http://localhost:4321  # CORS engedélyezett eredetek

# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

| Változó | Kötelező | Leírás |
|---------|----------|--------|
| `DATABASE_URL` | Igen | PostgreSQL kapcsolati string |
| `SECRET_KEY` | Igen | JWT aláíró kulcs — élesben **egyedi és véletlenszerű** legyen |
| `BASE_URL` | Igen | A platform publikus URL-je (tanúsítványokhoz, QR kódokhoz) |
| `GITHUB_CLIENT_ID` | Igen | GitHub OAuth App kliens azonosító |
| `GITHUB_CLIENT_SECRET` | Igen | GitHub OAuth App kliens titkos kulcs |
| `GITHUB_ORG` | Nem | GitHub szervezet neve (Classroom integrációhoz) |
| `GITHUB_WEBHOOK_SECRET` | Nem | GitHub webhook titkos kulcs (Classroom webhookhoz) |
| `DB_USER` | Igen | PostgreSQL felhasználónév (docker-compose használja) |
| `DB_PASSWORD` | Igen | PostgreSQL jelszó (docker-compose használja) |
| `DB_NAME` | Igen | PostgreSQL adatbázisnév (docker-compose használja) |
| `ENVIRONMENT` | Nem | `development` vagy `production` — élesben kikapcsolja a Swagger UI-t |
| `ALLOWED_ORIGINS` | Nem | CORS engedélyezett eredetek, vesszővel elválasztva (pl. `https://yourdomain.com`) |

---

## Adatbázis és migrációk

A projekt **Alembic**-et használ az adatbázis migrációkhoz.

```bash
# Összes függőben lévő migráció futtatása
cd backend
alembic upgrade head

# Új migráció létrehozása modell módosítás után
alembic revision --autogenerate -m "leírás a változásról"

# Aktuális migrációs állapot ellenőrzése
alembic current

# Egy lépés visszavonása
alembic downgrade -1
```

Docker-en keresztül:

```bash
docker compose exec backend alembic upgrade head
```

---

## GitHub OAuth beállítás

1. Nyisd meg a [GitHub Developer Settings](https://github.com/settings/developers) oldalt
2. Kattints a **New OAuth App** gombra
3. Töltsd ki:
   - **Application name:** `OpenSchool` (vagy bármilyen név)
   - **Homepage URL:** `http://localhost` (vagy az éles domain)
   - **Authorization callback URL:** `http://localhost/api/auth/callback`
4. Kattints a **Register application** gombra
5. Másold ki a **Client ID**-t és generálj **Client Secret**-et
6. Add hozzá a `.env` fájlhoz:
   ```
   GITHUB_CLIENT_ID=Ov23li...
   GITHUB_CLIENT_SECRET=25a23e268e...
   ```

> **Fontos:** Éles környezethez hozz létre külön OAuth App-ot az éles domain-nel mint callback URL: `https://yourdomain.com/api/auth/callback`

---

## Tesztek futtatása

```bash
cd backend

# Összes teszt futtatása
pytest -v

# Adott tesztfájl futtatása
pytest tests/test_auth.py -v

# Lefedettségi riporttal
pytest --cov=app --cov-report=term-missing
```

A CI pipeline minden push és PR esetén automatikusan futtatja a teszteket.

---

## Éles telepítés (VPS)

### Automatizált telepítés (ajánlott)

A teljes VPS beállítás automatizálható egyetlen szkripttel:

```bash
# SSH belépés a VPS-re
ssh root@your-vps-ip

# Automatizált bootstrap futtatása — végigvezet minden lépésen:
# Docker, tűzfal, repo klónozás, .env.prod generálás, SSL, seed data, cron
curl -fsSL https://raw.githubusercontent.com/ghemrich/openschool-platform/main/scripts/bootstrap-vps.sh -o bootstrap-vps.sh
bash bootstrap-vps.sh
```

A szkript interaktívan kérdezi a domain-t, GitHub OAuth adatokat, és automatikusan:
- Telepíti a Dockert + tűzfalat (UFW: 22, 80, 443 nyitva)
- Létrehozza a deploy usert és a projekt könyvtárat
- Klónozza a repót és erős jelszavakkal generálja a `.env.prod`-ot
- Elindítja a szolgáltatásokat és futtatja a migrációkat
- Beállítja a Let's Encrypt SSL-t
- Telepíti a karbantartási cron job-okat (`provision.sh`)

A bootstrap után futtasd a biztonsági ellenőrzést:

```bash
./scripts/security-check.sh
```

> A telepítés részleteit lásd alább, ha manuálisan szeretnéd elvégezni.

### Manuális telepítés

#### 1. Szerver előkészítése

```bash
# SSH belépés a VPS-re
ssh root@your-vps-ip

# Rendszerfrissítés és alap csomagok
apt-get update && apt-get install -y curl git ufw

# Docker telepítése (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh

# Docker Compose plugin telepítése (ha nincs benne)
apt-get install -y docker-compose-plugin
```

#### 1b. Tűzfal beállítása (UFW)

```bash
# Tűzfal engedélyezése — csak SSH, HTTP és HTTPS portok
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Ellenőrzés
ufw status
```

> A PostgreSQL port (5432) **nem** szabad kívülről elérhető legyen — a Docker-en belül érik el a szolgáltatások.

#### 1c. Deploy felhasználó létrehozása

Ne futtasd a szolgáltatásokat root-ként — hozz létre egy dedikált deploy felhasználót:

```bash
# Deploy felhasználó létrehozása
useradd -m -s /bin/bash openschool

# Docker csoport hozzáadása (konténerek kezeléshez)
usermod -aG docker openschool

# Projekt könyvtár létrehozása és birtokba adása
mkdir -p /opt/openschool
chown openschool:openschool /opt/openschool
```

A deploy felhasználónak **nem kell** sudo jogosultság. A Docker csoport tagság elég a konténerek kezeléséhez.

> **Megjegyzés:** Az SSH kulcs alapú bejelentkezést is be kell állítani ehhez a felhasználóhoz, ha CI/CD-t használsz (lásd [Deploy SSH kulcs CI/CD-hez](#deploy-ssh-kulcs-cicd-hez)).

### 2. Klónozás és konfigurálás

```bash
# Váltás a deploy felhasználóra
su - openschool
cd /opt/openschool

git clone git@github.com:ghemrich/openschool-platform.git .
```

#### `.env.prod` fájl létrehozása

Az éles környezeti fájl neve `.env.prod` (nem `.env`), és szimlinkelve lesz:

```bash
# Erős jelszavak generálása
DB_PASS=$(openssl rand -base64 24)
SECRET=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 20)

# .env.prod fájl létrehozása
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
EOF

# Jogosultsagok (csak a tulajdonos olvashatja)
chmod 600 .env.prod

# Szimlink létrehozása a docker-compose kompatibilitáshoz
ln -sf .env.prod .env
```

> ⚠️ **Fontos:** A `.env.prod` fájl tartalmazza az összes titkos kulcsot. Soha ne commitold, és állítsd `chmod 600`-ra.

### 3. DNS konfiguráció

Irányítsd a domaint a VPS IP-címére:

| Típus | Név | Érték |
|-------|-----|-------|
| A | `yourdomain.com` | `VPS_IP_CÍM` |
| A | `www` | `VPS_IP_CÍM` |

Várd meg a DNS propagációt (akár 48 óra, általában percek).

### 4. Szolgáltatások indítása

```bash
docker compose -f docker-compose.prod.yml up --build -d

# Migrációk futtatása
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Ellenőrzés
curl http://localhost/health
```

### 5. Kezdeti adatok betöltése (opcionális)

```bash
docker compose exec db psql -U openschool -d openschool <<'SQL'
INSERT INTO courses (name, description) VALUES
  ('Python Alapok', '13 hetes bevezető kurzus a Python programozásba.'),
  ('Backend FastAPI', '25 hetes backend fejlesztő kurzus FastAPI keretrendszerrel.'),
  ('Projekt Labor', 'A OpenSchool platform felépítése az alapoktól az éles üzemig.');
SQL
```

---

## SSH biztonság

Az éles szerveren az SSH jelszavas bejelentkezést **ki kell kapcsolni** — csak kulcs alapú hitelesítés engedélyezett. Ez megakadályozza a brute-force támadásokat.

### 1. SSH kulcs másolása a VPS-re

Ha még nincs SSH kulcsod, generálj egyet a helyi gépen:

```bash
# Kulcs generálása (ha még nincs)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Kulcs másolása a VPS-re (jelszóval kell bejelentkezni ehhez utoljára)
ssh-copy-id root@VPS_IP
```

### 2. Jelszavas bejelentkezés letiltása

Miután a kulcs alapú bejelentkezés működik, tiltsd le a jelszavas hozzáférést:

```bash
ssh root@VPS_IP

# sshd_config módosítása
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' /etc/ssh/sshd_config

# SSH szolgáltatás újraindítása
systemctl restart sshd
```

### 3. Ellenőrzés

```bash
# Egy másik terminálból próbálj meg jelszóval belépni — el kell utasítania
ssh -o PubkeyAuthentication=no root@VPS_IP
# → Permission denied (publickey).
```

> ⚠️ **Fontos:** Ne zárd be az aktuális SSH munkamenetet, amíg nem ellenőrizted, hogy a kulcs alapú bejelentkezés működik egy másik terminálból! Ha elrontod, kizárhatod magad a szerverről.

---

## DNS és Cloudflare konfiguráció

Ha Cloudflare-t használsz DNS szolgáltatóként és CDN/DDoS védelemként:

### 1. DNS rekord beállítása

Cloudflare Dashboard → DNS → Records:

| Típus | Név | Tartalom | Proxy |
|-------|-----|----------|-------|
| A | `@` (vagy `yourdomain.com`) | `VPS_IP_CÍM` | Proxied (narancssárga felhő) |

### 2. SSL/TLS mód

Cloudflare Dashboard → SSL/TLS → Overview:

- **Full (Strict)** — ez az ajánlott beállítás
- Ez megköveteli, hogy az origin szerveren (VPS) érvényes SSL tanúsítvány legyen (Let's Encrypt)
- Cloudflare HTTPS-sel csatlakozik a VPS-hez, a látogatók is HTTPS-t kapnak

> ⚠️ **Ne használj "Flexible" módot** éles környezetben! Flexible módban a Cloudflare és a VPS közötti forgalom titkosítatlan HTTP — ez biztonsági kockázat.

### 3. SSL/TLS módok összehasonlítása

| Mód | Cloudflare → Origin | Tanúsítvány kell? | Biztonság |
|-----|---------------------|-------------------|----------|
| Off | HTTP | Nem | ❌ Nincs titkosítás |
| Flexible | HTTP | Nem | ⚠️ Félig titkosított |
| Full | HTTPS | Bármilyen (self-signed is) | ✅ Titkosított |
| **Full (Strict)** | **HTTPS** | **Érvényes (Let's Encrypt)** | **✅✅ Ajánlott** |

### 4. SSL tanúsítvány igénylés Cloudflare mögül

A Let's Encrypt certbot standalone módja **nem működik** aktív Cloudflare proxyval, mert a Cloudflare elkapja a HTTP kéréseket. A megoldás:

1. **Ideiglenesen kapcsold ki** a Cloudflare proxyt (narancssárga felhő → szürke felhő / "DNS only")
2. Futtasd a certbot-ot (lásd [SSL/TLS Let's Encrypt-tel](#ssltls-lets-encrypttel))
3. **Kapcsold vissza** a Cloudflare proxyt (szürke → narancssárga felhő)
4. Állítsd az SSL módot **Full (Strict)**-re

> **Megjegyzés:** A tanúsítvány megújításkor is ideiglenesen ki kell kapcsolni a Cloudflare proxyt, vagy használj DNS-01 challenge-t (lásd alább az automatikus megújításnál).

---

## SSL/TLS Let's Encrypt-tel

### A) Certbot standalone (legegyszerűbb)

```bash
# Certbot telepítése
sudo apt-get install certbot

# nginx ideiglenes leállítása
docker compose -f docker-compose.prod.yml stop nginx

# Tanúsítvány igénylése
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# A tanúsítvány fájlok itt lesznek:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Frissítsd az `nginx/nginx.conf` fájlt SSL-hez:

```nginx
# HTTP — /health átengedi (Docker healthcheck-hez), minden mást HTTPS-re irányít
server {
    listen 80;

    location /health {
        proxy_pass http://backend/health;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS — fő kiszolgáló
server {
    listen 443 ssl;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... meglévő location blokkok (api, health, verify, stb.) ...
}
```

> **Fontos:** A port 80-as szerver blokkban a `/health` endpoint továbbra is elérhető marad — ez szükséges a Docker healthcheck és a belső monitoring számára. Minden más kérést HTTPS-re irányít.

Csatold a tanúsítványokat a `docker-compose.prod.yml`-ben:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

### B) Reverse proxy Caddy-vel vagy Traefik-kel

Ha automatikus SSL-t szeretnél, fontold meg az nginx cseréjét [Caddy](https://caddyserver.com/)-re, amely automatikusan kezeli a Let's Encrypt-et.

### Automatikus megújítás

```bash
# Megújítás tesztelése
sudo certbot renew --dry-run

# Cron job hozzáadása az automatikus megújításhoz
echo "0 3 * * * certbot renew --quiet && docker compose -f /opt/openschool/docker-compose.prod.yml restart nginx" | sudo tee /etc/cron.d/certbot-renew
```

> **Cloudflare használata esetén:** A standalone megújításhoz az nginx-t le kell állítani és a Cloudflare proxyt ideiglenesen ki kell kapcsolni. Alternatívaként a `certbot` DNS-01 challenge pluginja (pl. `certbot-dns-cloudflare`) képes megújítani a tanúsítványt a Cloudflare proxy kikapcsolása nélkül:
>
> ```bash
> # Cloudflare DNS plugin telepítése
> apt-get install python3-certbot-dns-cloudflare
>
> # API token fájl létrehozása (Cloudflare Dashboard → API Tokens → Edit zone DNS)
> cat > /etc/letsencrypt/cloudflare.ini << EOF
> dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN
> EOF
> chmod 600 /etc/letsencrypt/cloudflare.ini
>
> # Tanúsítvány igénylése DNS-01 challenge-sel (proxy maradhat bekapcsolva)
> certbot certonly --dns-cloudflare \
>   --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
>   -d yourdomain.com
> ```

---

## Staging telepítés

A staging környezet az éles rendszer tükörképe, ahol a `develop` branch-et teszteljük deploy előtt. A staging és a production **teljesen elkülönített** — saját adatbázis, saját GitHub OAuth app, saját domain — de **ugyanazon a VPS-en** futnak.

### Architektúra

A staging a production mellett fut ugyanazon a VPS-en, megosztott Docker hálózaton keresztül:

```
Internet
  │
  ▼
Cloudflare (SSL termination + CDN)
  │
  ▼ HTTPS
Production nginx (docker-compose.prod.yml)
  ├── yourdomain.com → backend (prod)
  └── staging.yourdomain.com ──► openschool-net ──► Staging nginx (docker-compose.staging.yml)
                                                       └── backend (staging)
```

- A **production nginx** kezeli az SSL-t mindkét domainhez (egyetlen Let's Encrypt tanúsítvány)
- A staging kéréseket az `openschool-net` Docker hálózaton keresztül proxy-zza a staging nginx konténerbe
- A **staging nginx** (`nginx-staging.conf`) csak HTTP-t szolgál ki — az SSL-t a production nginx terminálja
- Minden más (backend, DB, frontend) teljesen elkülönített

### 1. GitHub OAuth app staging-hez

A staging-nek **külön** GitHub OAuth alkalmazás kell (a callback URL eltér):

1. [GitHub Settings > Developer settings > OAuth Apps > New](https://github.com/settings/developers)
2. Beállítások:
   - **Application name:** `OpenSchool Staging`
   - **Homepage URL:** `https://staging.yourdomain.com`
   - **Authorization callback URL:** `https://staging.yourdomain.com/api/auth/callback`
3. Jegyezd fel a `Client ID` és `Client Secret` értékeket

### 2. Docker hálózat létrehozása

A production és staging nginx konténerek egy közös Docker hálózaton kommunikálnak:

```bash
docker network create openschool-net
```

> Ez a hálózat mindkét compose stack-ben `external: true`-ként van hivatkozva, tehát a compose nem hozza létre automatikusan — **előre létre kell hozni**.

### 3. Staging könyvtár és klónozás

```bash
# Staging könyvtár létrehozása (elkülönítve a /opt/openschool production-től)
sudo mkdir -p /opt/openschool-staging
sudo chown openschool:openschool /opt/openschool-staging

# Klónozás (develop branch)
su - openschool
cd /opt/openschool-staging
git clone -b develop git@github.com:ghemrich/openschool-platform.git .
```

### 4. Környezeti változók

Hozz létre `.env.staging` fájlt, majd szimlinkelj:

```bash
cd /opt/openschool-staging

# Erős jelszavak generálása
DB_PASS=$(openssl rand -base64 24)
SECRET=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 20)

cat > .env.staging << EOF
DB_USER=openschool_staging
DB_PASSWORD=$DB_PASS
DB_NAME=openschool_staging
DATABASE_URL=postgresql://openschool_staging:${DB_PASS}@db:5432/openschool_staging
SECRET_KEY=$SECRET
BASE_URL=https://staging.yourdomain.com
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
GITHUB_CLIENT_ID=staging_oauth_client_id
GITHUB_CLIENT_SECRET=staging_oauth_client_secret
GITHUB_WEBHOOK_SECRET=$WEBHOOK_SECRET
EOF

chmod 600 .env.staging
ln -sf .env.staging .env
```

> ⚠️ **Fontos:** A staging és production adatbázis **külön** kell legyen (`openschool_staging` vs `openschool`). Soha ne használj production adatokat staging-en.

### 5. Compose és nginx fájlok

A repóban két dedikált fájl biztosítja a staging működését:

- **`docker-compose.staging.yml`** — önálló compose fájl a staging stack-hez (saját projekt neve: `openschool-staging`, saját volume-ok, nincs publikált port — a staging nginx az `openschool-net` hálózaton érhető el a production nginx számára)
- **`nginx/nginx-staging.conf`** — HTTP-only nginx konfig (nincs SSL — a production nginx terminálja az SSL-t)

Ezek a fájlok már a repóban vannak, nem kell létrehozni.

### 6. Production konfig frissítése

A production stack-et is frissíteni kell, hogy a staging-et kiszolgálja:

#### `docker-compose.prod.yml` — hálózat hozzáadása

Az nginx szolgáltatás csatlakozzon az `openschool-net` hálózathoz is:

```yaml
nginx:
  # ... meglévő konfig ...
  networks:
    - default
    - openschool-net

networks:
  openschool-net:
    external: true
```

#### `nginx/nginx.conf` — staging proxy blokkok

A production nginx-hez két új server blokk kell (HTTP + HTTPS) a staging domainhez:

```nginx
# HTTP — staging health + redirect
server {
    listen 80;
    server_name staging.yourdomain.com;

    resolver 127.0.0.11 valid=30s ipv6=off;
    set $staging_backend http://openschool-staging-nginx-1;

    location /health {
        proxy_pass $staging_backend;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS — staging proxy
server {
    listen 443 ssl;
    server_name staging.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    resolver 127.0.0.11 valid=30s ipv6=off;
    set $staging_backend http://openschool-staging-nginx-1;

    location / {
        proxy_pass $staging_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> A `resolver 127.0.0.11` a Docker belső DNS-e. A `set $staging_backend` változóval oldja meg az nginx, hogy a staging konténer DNS neve runtime-ban legyen feloldva (nem induláskor).

### 7. DNS konfiguráció

Hozz létre egy `A` rekordot a staging subdomainhez:

```
staging.yourdomain.com  →  A  →  VPS_IP
```

Ha Cloudflare-t használsz: először állítsd **DNS only** módra (szürke felhő) az SSL tanúsítvány igényléshez, utána kapcsold **Proxied**-re.

### 8. SSL tanúsítvány bővítése

A meglévő Let's Encrypt tanúsítványt ki kell bővíteni a staging domainnel:

```bash
# Production nginx leállítása (80-as port felszabadítása)
cd /opt/openschool
docker compose -f docker-compose.prod.yml stop nginx

# Tanúsítvány bővítése az --expand kapcsolóval
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d staging.yourdomain.com \
  --expand

# Production nginx újraindítása
docker compose -f docker-compose.prod.yml start nginx
```

> A `--expand` kapcsoló a meglévő tanúsítványhoz adja hozzá az új domaint, nem cseréli le. Cloudflare használata esetén ideiglenesen ki kell kapcsolni a proxyt (DNS only), majd az igénylés után vissza kell kapcsolni.

### 9. Production újraindítása

A hálózati és nginx változtatások után újra kell indítani a production stack-et:

```bash
cd /opt/openschool
git pull origin main
docker compose -f docker-compose.prod.yml up --build -d
```

### 10. Staging indítása

```bash
cd /opt/openschool-staging

# Staging konténerek buildelése és indítása
docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d

# Migráció futtatása
docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head

# Ellenőrzés
curl -f https://staging.yourdomain.com/health
# → {"status": "ok"}
```

> Ha az Alembic `DuplicateTable` hibát ad (mert a SQLAlchemy modellek már létrehozták a táblákat), futtasd: `docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic stamp head`

### 11. Deploy folyamat

A staging deploy a `develop` branch-ről történik:

```bash
cd /opt/openschool-staging
git pull origin develop
docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head
curl -f https://staging.yourdomain.com/health
```

**CD pipeline staging deploy-jal (opcionális):**

```yaml
# .github/workflows/cd.yml — staging job hozzáadása
staging-deploy:
  runs-on: ubuntu-latest
  needs: test
  if: github.ref == 'refs/heads/develop' && vars.STAGING_HOST != ''
  environment: staging
  steps:
    - name: Deploy to staging
      uses: appleboy/ssh-action@v1
      with:
        host: ${{ vars.STAGING_HOST }}
        username: ${{ secrets.STAGING_USER }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          set -e
          cd /opt/openschool-staging
          git pull origin develop
          docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
          docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head
          sleep 5
          curl -f https://staging.yourdomain.com/health
          echo "Staging deploy successful!"
```

Ehhez a GitHub repo-ban be kell állítani:
- **Environment:** `staging` (Settings > Environments)
- **Variables:** `STAGING_HOST`
- **Secrets:** `STAGING_USER`, `STAGING_SSH_KEY`

### 12. Migráció tesztelés staging-en

A staging elsődleges célja az adatbázis migrációk tesztelése éles deploy előtt:

1. **Migráció generálása** a fejlesztői gépen (`alembic revision --autogenerate`)
2. **PR nyitása** `develop`-ra → CI futtatja a teszteket
3. **Merge `develop`-ba** → staging deploy (manuális vagy automatikus)
4. **Migráció futtatása staging-en** → ellenőrzés, hogy sikeres-e
5. **Funkcionális teszt** staging-en (manuális)
6. **Merge `main`-be** → production deploy

### 13. Staging vs Production összehasonlítás

| Szempont | Staging | Production |
|----------|---------|------------|
| Branch | `develop` | `main` |
| Domain | `staging.yourdomain.com` | `yourdomain.com` |
| Compose fájl | `docker-compose.staging.yml` | `docker-compose.prod.yml` |
| Nginx konfig | `nginx-staging.conf` (HTTP only) | `nginx.conf` (SSL + staging proxy) |
| Adatbázis | `openschool_staging` | `openschool` |
| GitHub OAuth | Külön app | Külön app |
| `ENVIRONMENT` | `staging` | `production` |
| Swagger UI | Elérhető (`/docs`) | Letiltva |
| SSL | Production nginx terminálja | Közvetlen Let's Encrypt |
| Hálózat | `openschool-net` (prod nginx-hez) | `openschool-net` + default |
| Deploy | Manuális / develop push | Automatikus main push |
| Cél | Tesztelés, review | Felhasználói forgalom |

---

## Karbantartás és provisioning

A telepítés után futtasd a `provision.sh` szkriptet a karbantartási infrastruktúra beállításához:

```bash
# Root-ként a VPS-en
sudo /opt/openschool/scripts/provision.sh
```

Ez a következőket állítja be:
1. **Backup könyvtár** — `/opt/openschool/backups/`
2. **Cron job-ok** — napi, heti, havi karbantartási feladatok (`/etc/cron.d/openschool-maintenance`)
3. **Karbantartási konfig** — `/etc/openschool-maintenance.conf`
4. **Fájl jogosultságok** — szkriptek futtathatóvá tétele, `.env.prod` védelme
5. **Log rotáció** — `/etc/logrotate.d/openschool`

### Karbantartási konfig szerkesztése

A `provision.sh` létrehoz egy konfigurációs fájlt a `/etc/openschool-maintenance.conf` helyen. Szerkeszd az SSL domain és a Discord értesítések beállításához:

```bash
sudo nano /etc/openschool-maintenance.conf
```

Fontos beállítások:

```bash
# SSL tanúsítvány lejárat figyelése (kötelező HTTPS esetén)
SSL_DOMAIN=yourdomain.com
SSL_WARNING_DAYS=30

# Discord értesítések (opcionális)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Backup konfiguráció (alapértelmezettek általában jók)
# BACKUP_DIR=/opt/openschool/backups
# BACKUP_RETENTION_DAYS=30
```

### Karbantartási parancsok

A beállítás után a karbantartó szkript elérhető:

```bash
# Szolgáltatások állapot ellenőrzése
./scripts/maintenance.sh health

# Kézi backup készítése
./scripts/maintenance.sh backup

# SSL tanúsítvány lejárat ellenőrzése
./scripts/maintenance.sh ssl-check

# Teljes napi karbantartás
./scripts/maintenance.sh full-daily
```

---

## Deploy SSH kulcs CI/CD-hez

A GitHub Actions CD pipeline SSH-val csatlakozik a VPS-hez. Ehhez egy dedikált SSH kulcspár kell a deploy felhasználóhoz.

### 1. SSH kulcspár generálása a VPS-en

```bash
# Deploy felhasználóként
su - openschool

# Ed25519 kulcspár generálása (jelszó nélkül a CI/CD automatizáláshoz)
ssh-keygen -t ed25519 -C "deploy@openschool" -f ~/.ssh/id_ed25519 -N ""

# Publikus kulcs hozzáadása az authorized_keys-hez
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Privát kulcs tartalmának kiíratása (ezt kell a GitHub Secrets-be másolni)
cat ~/.ssh/id_ed25519
```

### 2. GitHub Actions titkok beállítása

GitHub repó → Settings → Secrets and variables → Actions:

**Secrets** (Settings → Secrets → New repository secret):

| Név | Érték |
|-----|-------|
| `VPS_USER` | `openschool` |
| `VPS_SSH_KEY` | A privát kulcs teljes tartalma (`-----BEGIN OPENSSH PRIVATE KEY-----` ... `-----END OPENSSH PRIVATE KEY-----`) |

**Variables** (Settings → Variables → New repository variable):

| Név | Érték |
|-----|-------|
| `VPS_HOST` | A VPS IP-címe (pl. `194.99.21.209`) |

### 3. Tesztelés

Push-olj a `main` ágra, és ellenőrizd, hogy a CD pipeline sikeresen csatlakozik és deploy-ol:

```bash
git push origin main
# → GitHub Actions → CD workflow → ellenőrizd a deploy lépést
```

> **Megjegyzés:** A `VPS_HOST` változó (nem secret!) vezérli, hogy a CD pipeline egyáltalán lefut-e. Ha nincs beállítva, a deploy lépés kihagyásra kerül.

---

## Biztonsági mentés

A `scripts/backup.sh` szkript biztonsági mentést készít:

```bash
# Kézi futtatás
./scripts/backup.sh

# Napi cron job beállítása (hajnali 3-kor fut)
echo "0 3 * * * /opt/openschool/scripts/backup.sh" | crontab -
```

A szkript:
- `pg_dump`-pal menti a PostgreSQL adatbázist
- `.sql.gz` formátumra tömöríti
- `/opt/openschool/backups/` mappába menti
- 30 napnál régebbi mentéseket törli

### Kézi mentés

```bash
docker compose exec db pg_dump -U openschool openschool | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Visszaállítás mentésből

```bash
gunzip < backup_20260310.sql.gz | docker compose exec -T db psql -U openschool openschool
```

---

## CI/CD Pipeline

### CI (Folyamatos integráció)

Minden push (`main`, `develop`) és PR esetén fut:

1. **Lint lépés** — `ruff check` és `ruff format --check` ellenőrzés
2. **Teszt lépés** — `pytest -v --tb=short` (csak ha a lint sikeres)

A tesztek SQLite-ot használnak, nem igényelnek PostgreSQL-t.

### CD (Folyamatos telepítés)

Push esetén a `main` ágra — **csak ha a tesztek sikeresek és a `VPS_HOST` be van állítva**:

1. Tesztek futtatása (gate)
2. SSH kapcsolat a VPS-hez
3. `git pull origin main`
4. Docker konténerek újraépítése
5. Alembic migrációk futtatása
6. Health check (`curl -f http://localhost:8000/health`)

Szükséges GitHub beállítások:

| Típus | Név | Leírás |
|-------|--------|--------|
| Variable | `VPS_HOST` | VPS IP-cím vagy hosztnév (Settings → Variables) |
| Secret | `VPS_USER` | SSH felhasználónév a VPS-en |
| Secret | `VPS_SSH_KEY` | Privát SSH kulcs a VPS eléréséhez |

Beállítás:
1. GitHub repó → Settings → Environments → `production` létrehozása
2. Settings → Secrets and variables → Actions → Secrets-be: `VPS_USER`, `VPS_SSH_KEY`
3. Settings → Secrets and variables → Actions → Variables-be: `VPS_HOST`
4. A következő push a `main`-re automatikusan telepít

---

## Hibaelhárítás

### Docker jogosultsági hiba

```bash
sudo usermod -aG docker $USER
# Jelentkezz ki és be (vagy indítsd újra a terminált)
```

### A 80-as port foglalt

```bash
# Keresd meg, mi használja a 80-as portot
sudo lsof -i :80
# Állítsd le, vagy módosítsd az nginx portot a docker-compose.yml-ben
```

### Adatbázis kapcsolódási hiba

```bash
# Ellenőrizd, hogy a db konténer fut-e
docker compose ps db
# Nézd meg a db logokat
docker compose logs db
```

### Frontend változások nem látszanak

```bash
# Frontend újraépítése
docker compose up --build frontend
# nginx újraindítása az új statikus fájlok betöltéséhez
docker compose restart nginx
```

### OAuth callback hiba

- Ellenőrizd a `GITHUB_CLIENT_ID` és `GITHUB_CLIENT_SECRET` értékeket a `.env`-ben
- Győződj meg róla, hogy az OAuth callback URL egyezik: `http://localhost/api/auth/callback` (fejlesztés) vagy `https://yourdomain.com/api/auth/callback` (éles)
- Nézd meg a backend logokat: `docker compose logs backend`

### Tanúsítvány PDF nem generálódik

- Ellenőrizd, hogy a `backend/data/` könyvtár létezik és írható
- Nézd meg a backend logokat a PDF generálási hibákért

### VPS újratelepítés után SSH host key hiba

Ha a VPS-t újratelepítették, az SSH kliens régi host key-t fog találni, és megtagadja a kapcsolatot:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

Megoldás:

```bash
# Régi host key törlése a helyi gépről
ssh-keygen -R VPS_IP

# Újra csatlakozás (elfogadja az új host key-t)
ssh root@VPS_IP
```

### Alembic migráció hiba: tábla már létezik

Ha a SQLAlchemy modellek automatikusan létrehozták a táblákat az `alembic upgrade head` előtt:

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "users" already exists
```

Megoldás — jelöld meg az aktuális állapotot a legutolsó migrációval:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic stamp head
```

Ez nem futtat migrációkat, csak beállítja az Alembic verziót, hogy szinkronban legyen a tényleges adatbázis állapottal.

### Cloudflare 522 Connection Timed Out

Ha a domain Cloudflare mögül 522 hibát ad:

1. **Konténerek futnak?** — `docker compose -f docker-compose.prod.yml ps`
2. **Portok nyitva?** — `sudo ufw status` (80 és 443 kell)
3. **SSL mód helyes?** — Cloudflare SSL/TLS → Full (Strict) módban a VPS-en HTTPS (port 443) kell
4. **nginx elérhető?** — `curl -v http://localhost/health` a VPS-ről
5. **Cloudflare proxy aktív?** — DNS rekordnál narancssárga felhő (Proxied) kell

Gyakori ok: Cloudflare Full/Full (Strict) módban a 443-as porton próbál csatlakozni, de az nginx-ben nincs SSL konfigurálva vagy a 443-as port nincs nyitva a tűzfalon.

---

## Éles rendszer biztonsági ellenőrzőlista

A biztonsági ellenőrzőlista futtatható automatikusan is:

```bash
./scripts/security-check.sh
```

Ez ellenőrzi a SECRET_KEY erősségét, ENVIRONMENT beállítást, CORS konfigurációt, DB jelszót, .env.prod jogosultságokat, HTTPS-t, tűzfalat, konténer állapotot, Swagger UI elérhetőségét, mentések frissességét és cron job-okat.

Manuális ellenőrzőlista:

| Elem | Ellenőrzés |
|------|------------|
| `SECRET_KEY` | Egyedi, véletlenszerű, legalább 32 karakter (`openssl rand -hex 32`) |
| `ENVIRONMENT` | `production` értékre állítva (kikapcsolja a Swagger UI-t) |
| `ALLOWED_ORIGINS` | Csak az éles domain(ek) vannak felsorolva |
| `GITHUB_WEBHOOK_SECRET` | Be van állítva, megegyezik a GitHub webhook konfigurációval |
| `DB_PASSWORD` | Erős, egyedi jelszó (nem az alapértelmezett) |
| HTTPS | Let's Encrypt tanúsítvány bekonfigurálva, HTTP→HTTPS átirányítás |
| OAuth callback | Az éles domain-re mutat (`https://yourdomain.com/api/auth/callback`) |
| Backup | Napi `pg_dump` cron job beállítva |
| Tűzfal | Csak 80/443 port nyitva kívülről, PostgreSQL (5432) nem elérhető |
| DNS | A domain A rekord a VPS IP-re mutat |
| SSH | Jelszavas bejelentkezés letiltva, csak kulcs alapú hitelesítés |
| Cloudflare SSL | Full (Strict) mód beállítva (ha Cloudflare-t használsz) |
