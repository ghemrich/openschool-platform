# OpenSchool Platform

[![CI](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Nyílt forráskódú oktatási platform, ahol a diákok valódi fejlesztői eszközökkel tanulnak programozni.

> **Az open source nem feature — az open source a tanterv.**

Nem csak a szoftver nyílt: a tananyag, az eszközök, az értékelés, a platform kódja — minden látható, minden módosítható.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Adatbázis:** PostgreSQL
- **Frontend:** Astro (statikus oldal generátor)
- **Infrastruktúra:** Docker Compose, nginx, GitHub Actions

## Gyors indítás

### Előfeltételek

- Docker és Docker Compose
- Python 3.12+ (lokális fejlesztéshez)

### Futtatás Docker-rel

```bash
# .env fájl létrehozása
cp .env.example .env

# Indítás
docker compose up --build -d

# Ellenőrzés
curl http://localhost:8000/health
```

### Lokális fejlesztés

```bash
# Virtuális környezet
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Tesztek futtatása
pytest -v

# Linter
ruff check . && ruff format --check .
```

### Makefile parancsok

```bash
make dev-setup  # Teljes fejlesztői környezet felállítása
make up         # Docker Compose indítás
make down       # Docker Compose leállítás
make test       # Tesztek futtatása
make migrate    # Alembic migrációk futtatása
make lint       # Ruff linter és formatter ellenőrzés
make format     # Kód formázása
make logs       # Docker logok követése
make clean      # Ideiglenes fájlok törlése
make changelog  # CHANGELOG.md generálása
```

A karbantartási parancsokért lásd: [Automatizálás](docs/automatizalas-beallitas.md)

## Projekt struktúra

```
openschool-platform/
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci.yml
├── Makefile
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   └── routers/
│   └── tests/
├── frontend/
└── nginx/
```

## API Endpoints

### Publikus

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/health` | GET | Health check |
| `/api/courses` | GET | Kurzusok listázása (lapozható) |
| `/api/courses/{id}` | GET | Kurzus részletei (modulok, feladatok) |
| `/api/verify/{cert_id}` | GET | Tanúsítvány publikus verifikáció |

### Autentikáció

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/auth/login` | GET | GitHub OAuth bejelentkezés |
| `/api/auth/callback` | GET | OAuth callback |
| `/api/auth/me` | GET | Aktuális felhasználó adatai |
| `/api/auth/refresh` | POST | Token frissítés |
| `/api/auth/logout` | POST | Kijelentkezés (refresh token törlése) |

### Dashboard (bejelentkezett felhasználó)

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/me/dashboard` | GET | Felhasználói dashboard (összes kurzus haladás) |
| `/api/me/courses` | GET | Beiratkozott kurzusok listája haladással |
| `/api/me/courses/{id}/progress` | GET | Kurzus részletes haladása (modulonként) |
| `/api/me/courses/{id}/progress` | POST | Feladat manuális teljesítés jelölése |
| `/api/me/sync-progress` | POST | Haladás szinkronizálása GitHub CI-ból |
| `/api/me/certificates` | GET | Tanúsítványok listája |
| `/api/me/courses/{id}/certificate` | POST | Tanúsítvány igénylése (befejezett kurzushoz) |
| `/api/me/certificates/{cert_id}/pdf` | GET | Tanúsítvány PDF letöltése |

### Kurzuskezelés (beiratkozott felhasználó)

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/courses/{id}/enroll` | POST | Beiratkozás kurzusra |
| `/api/courses/{id}/unenroll` | POST | Leiratkozás kurzusról |
| `/api/courses/{id}/students` | GET | Beiratkozott diákok listája (mentor/admin) |

### Admin

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/admin/stats` | GET | Platform statisztikák |
| `/api/admin/users` | GET | Felhasználók listázása (lapozható, rendezhető) |
| `/api/admin/users/{id}/role` | PATCH | Felhasználó szerepkör módosítása |
| `/api/courses` | POST | Kurzus létrehozása |
| `/api/courses/{id}` | PUT | Kurzus szerkesztése |
| `/api/admin/courses/{id}` | DELETE | Kurzus törlése (kaszkád) |
| `/api/courses/{id}/modules` | POST | Modul hozzáadása |
| `/api/admin/modules/{id}` | DELETE | Modul törlése |
| `/api/courses/{id}/modules/{mid}/exercises` | POST | Feladat hozzáadása |
| `/api/admin/exercises/{id}` | DELETE | Feladat törlése |

### Webhook

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/webhooks/github` | POST | GitHub workflow_run webhook fogadása |

## Hozzájárulás

Szívesen fogadjuk a hozzájárulásokat! Olvasd el a [CONTRIBUTING.md](CONTRIBUTING.md) fájlt a részletekért.

## Dokumentáció

| Dokumentum | Leírás |
|---|---|
| [Architektúra](docs/architektura.md) | Rendszer felépítés, adatmodell, auth folyamat, API struktúra |
| [Telepítési útmutató](docs/telepitesi-utmutato.md) | Helyi fejlesztés, staging, éles VPS telepítés, SSL, backup |
| [Fejlesztői útmutató](docs/fejlesztoi-utmutato.md) | Környezet beállítás, VS Code, pre-commit, git-cliff, Docker, CI/CD, logok |
| [Backend fejlesztés](docs/backend-fejlesztes.md) | Python venv, FastAPI routers, modellek, Ruff, pytest, Alembic migrációk |
| [Frontend fejlesztés](docs/frontend-fejlesztes.md) | Astro oldalak, komponensek, kliens JS, CSS, admin panel, auth flow |
| [Jövőkép és fejlesztési terv](docs/jovokep-es-fejlesztesi-terv.md) | Kurzusok, megvalósított funkciók, roadmap |
| [Felhasználói útmutató](docs/felhasznaloi-utmutato.md) | Oldalak, gombok, felhasználói folyamatok, admin panel |
| [GitHub Classroom integráció](docs/github-classroom-integraciot.md) | Feladatok összekötése, repo_prefix, webhook, tanári útmutató |
| [Karbantartás](docs/karbantartas-utmutato.md) | Függőségkezelés, monitoring, backup, biztonsági audit, incidenskezelés |
| [Automatizálás](docs/automatizalas-beallitas.md) | Cron job-ok, VPS bootstrap, Discord értesítések, secrets kezelés |
| [Discord integráció](docs/discord-integracio.md) | Discord szerver, webhook, CI/CD értesítések, csatornastruktúra |
| [Dokumentálás](docs/dokumentacios-utmutato.md) | Docstring-ek, API docs, Markdown konvenciók, navsáv, CHANGELOG |
| [Hozzájárulás](CONTRIBUTING.md) | Fork, branch stratégia, PR küldés, kódstílus |

A `good first issue` címkéjű [issue-k](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) ideálisak kezdőknek.

## Licensz

A projekt az [MIT License](LICENSE) alatt érhető el.
