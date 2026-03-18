# OpenSchool Platform

[![CI](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Nyílt forráskódú oktatási platform, ahol a tanulók valódi fejlesztői eszközökkel tanulnak programozni.

> **Az open source nem feature — az open source a tanterv.**

Nem csak a szoftver nyílt: a tananyag, az eszközök, az értékelés, a platform kódja — minden látható, minden módosítható.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Adatbázis:** PostgreSQL
- **Frontend:** React 19 + TypeScript + Vite (SPA)
- **Tesztelés:** pytest (backend), Vitest + React Testing Library (frontend)
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

Lokális fejlesztéshez lásd: [Telepítés és fejlesztői környezet](docs/setup.md)

## Közösség

Csatlakozz a Discord szerverünkhöz: [discord.gg/BrKd45S6](https://discord.gg/BrKd45S6)

## Hozzájárulás

Szívesen fogadjuk a hozzájárulásokat! Lásd: [CONTRIBUTING.md](CONTRIBUTING.md)

## Dokumentáció

| Dokumentum | Leírás |
|---|---|
| [Telepítés](docs/setup.md) | Fejlesztői környezet, env vars, Docker, Makefile |
| [Architektúra](docs/architecture.md) | Rendszer felépítés, adatmodell, auth, infrastruktúra |
| [Backend](docs/backend.md) | FastAPI routers, services, Ruff, pytest, Alembic |
| [Frontend](docs/frontend.md) | React + TypeScript, oldalak, API, tesztelés |
| [Telepítés és üzemeltetés](docs/deployment.md) | VPS, SSH, DNS, SSL, CI/CD, staging, cron, secrets |
| [Karbantartás](docs/operations.md) | Workflow, minőségkapuk, monitoring, incidenskezelés |
| [API referencia](docs/api.md) | Összes végpont, sémák, státuszkódok |
| [Adatbázis séma](docs/database.md) | Táblák, kapcsolatok, migrációk |
| [Integrációk](docs/integrations.md) | Discord, GitHub Classroom |
| [Roadmap](docs/roadmap.md) | Jövőkép, megvalósított és tervezett funkciók |

### Kapcsolódó repók

| Repó | Leírás |
|---|---|
| [openschool-knowledge](https://github.com/ghemrich/openschool-knowledge) | Kurzusanyagok, útmutatók, vizsgák, értékelési módszertanok |

A `good first issue` címkéjű [issue-k](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) ideálisak kezdőknek.

## Licensz

A projekt az [MIT License](LICENSE) alatt érhető el.
