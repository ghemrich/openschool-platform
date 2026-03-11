# OpenSchool Platform — Dokumentálási útmutató

> 📖 **Dokumentáció:** [Főoldal](../README.md) · [Architektúra](architektura.md) · [Telepítés](telepitesi-utmutato.md) · [Fejlesztői útmutató](fejlesztoi-utmutato.md) · [Backend](backend-fejlesztes.md) · [Frontend](frontend-fejlesztes.md) · [Roadmap](jovokep-es-fejlesztesi-terv.md) · [Felhasználói útmutató](felhasznaloi-utmutato.md) · [GitHub Classroom](github-classroom-integraciot.md) · [Karbantartás](karbantartas-utmutato.md) · [Automatizálás](automatizalas-beallitas.md) · [Discord](discord-integracio.md) · **Dokumentálás** · [Hozzájárulás](../CONTRIBUTING.md)

Ez az útmutató leírja, hogyan kell dokumentálni a kódot és a projektet. Minden fejlesztő felelős azért, hogy a változtatásai dokumentáltak legyenek — a kódban és a docs mappában egyaránt.

---

## Tartalomjegyzék

1. [Alapelv: a kód és a dokumentáció együtt változik](#1-alapelv-a-kód-és-a-dokumentáció-együtt-változik)
2. [Python kód dokumentálása](#2-python-kód-dokumentálása)
3. [Frontend kód dokumentálása](#3-frontend-kód-dokumentálása)
4. [API végpontok dokumentálása](#4-api-végpontok-dokumentálása)
5. [Docs mappa karbantartása](#5-docs-mappa-karbantartása)
6. [Markdown konvenciók](#6-markdown-konvenciók)
7. [Navigációs sáv karbantartása](#7-navigációs-sáv-karbantartása)
8. [Változásnapló (CHANGELOG)](#8-változásnapló-changelog)
9. [README.md karbantartása](#9-readmemd-karbantartása)
10. [Ellenőrzőlista (PR előtt)](#10-ellenőrzőlista-pr-előtt)

---

## 1. Alapelv: a kód és a dokumentáció együtt változik

> **Minden PR-nek, ami funkciót ad hozzá, API-t módosít, vagy konfigurációt változtat, tartalmaznia kell a dokumentáció frissítését is.**

| Változtatás típusa | Szükséges dokumentáció |
|---------------------|------------------------|
| Új API végpont | Docstring + README API tábla + backend-fejlesztes.md |
| Új oldal (frontend) | frontend-fejlesztes.md oldalak szekció |
| Új modell/tábla | Docstring + backend-fejlesztes.md adatmodell |
| Konfiguráció változás | `.env.example` + telepitesi-utmutato.md |
| Új szkript | Szkript fejléc komment + README vagy releváns doc |
| Új Makefile target | fejlesztoi-utmutato.md Makefile szekció |
| Architekturális döntés | architektura.md |
| Bug fix | Csak ha a viselkedés dokumentálva volt és változott |

---

## 2. Python kód dokumentálása

### Docstring-ek

Minden publikus függvénynek, osztálynak és modulnak legyen docstring-je. A Google stílust használjuk:

```python
def enroll_student(db: Session, user_id: int, course_id: int) -> Enrollment:
    """Beiratkoztat egy diákot egy kurzusra.

    Ellenőrzi, hogy a diák nincs-e már beiratkozva. Ha igen, HTTPException-t dob.

    Args:
        db: Adatbázis session.
        user_id: A diák azonosítója.
        course_id: A kurzus azonosítója.

    Returns:
        Az új Enrollment objektum.

    Raises:
        HTTPException: 409, ha a diák már beiratkozott.
    """
```

### Mikor kell docstring?

| Elem | Docstring kötelező? |
|------|-------------------|
| Router végpont (`@router.get/post`) | ✅ Igen — FastAPI Swagger-ben jelenik meg |
| Service függvény | ✅ Igen |
| Modell osztály | ✅ Igen — tábla és mezők célja |
| Belső helper (privát, `_` prefix) | ❌ Nem kötelező — ha a név nem egyértelmű, igen |
| Teszt függvény | ❌ Nem — a teszt neve legyen leíró |

### Inline kommentek

Inline kommentet **csak akkor** írj, ha a kód célja nem egyértelmű a kódból:

```python
# ✅ Jó — magyaráz egy nem nyilvánvaló döntést
# Az UTC-t használjuk, mert a tanúsítványok időzónafüggetlenek
issued_at = datetime.now(UTC)

# ❌ Rossz — a kód magáért beszél
# Növeljük a számlálót
counter += 1
```

### Típusannotáció

A típusannotáció ajánlott minden publikus függvénynél:

```python
def get_course_progress(db: Session, user_id: int, course_id: int) -> float:
    ...
```

---

## 3. Frontend kód dokumentálása

### Astro komponensek

Az Astro komponensek fejlécében a frontmatter (`---`) részben kommentezd a props-okat:

```astro
---
// ProgressBar.astro
// Haladási sáv megjelenítése százalékos értékkel.
// Props:
//   percentage (number) — 0-100 közötti érték
//   label (string) — opcionális felirat a sáv felett

const { percentage, label } = Astro.props;
---
```

### JavaScript modulok

A `src/lib/` mappában lévő JS fájlok fejlécébe írj egy egysoros leírást:

```javascript
// api.js — Közös API hívások a backendhez (fetch wrapper, auth header kezelés)
```

Összetett függvények felett használj JSDoc-ot:

```javascript
/**
 * Kurzus részleteinek és a felhasználó haladásának betöltése.
 * @param {string} courseId — A kurzus slug-ja.
 * @returns {Promise<{course: Object, progress: Object}>}
 */
async function loadCourseDetail(courseId) { ... }
```

### CSS

A `src/styles/global.css` fájlban a szekciók kommenttel vannak tagolva — ezt a konvenciót tartsd meg:

```css
/* ============================================
   LAYOUT — Fő elrendezés, grid, flexbox
   ============================================ */
```

---

## 4. API végpontok dokumentálása

### FastAPI Swagger

A FastAPI automatikusan generálja a Swagger UI-t a docstring-ekből. Minden router végpontnak legyen:

1. **Docstring** — a Swagger leírásban jelenik meg
2. **`summary`** paraméter — rövid, egysoros leírás a Swagger listában
3. **Response model** — `response_model=` a válasz típusához

```python
@router.get("/courses/{course_id}", response_model=CourseResponse, summary="Kurzus részletei")
async def get_course(course_id: int, db: Session = Depends(get_db)):
    """Visszaadja egy kurzus részletes adatait.

    Tartalmazza a modulokat, gyakorlatokat és a kurzus metaadatait.
    """
```

### README API tábla

Amikor új végpontot adsz hozzá, frissítsd a `README.md` API végpontok táblázatát is:

```markdown
| Metódus | Útvonal | Leírás |
|---------|---------|--------|
| GET | /api/courses/{id} | Kurzus részletei |
```

---

## 5. Docs mappa karbantartása

### Dokumentum struktúra

```
docs/
├── architektura.md            # Rendszer architektúra, adatmodell
├── automatizalas-beallitas.md  # VPS automatizálás, cron, monitoring
├── backend-fejlesztes.md      # Backend fejlesztői útmutató
├── discord-integracio.md       # Discord szerver, webhook, bot
├── dokumentacios-utmutato.md  # ← Ez a dokumentum
├── fejlesztoi-utmutato.md     # Közös fejlesztői útmutató (Docker, CI/CD, stb.)
├── felhasznaloi-utmutato.md   # Felhasználói útmutató (UI, funkciók)
├── frontend-fejlesztes.md     # Frontend fejlesztői útmutató
├── github-classroom-integraciot.md  # GitHub Classroom tanári útmutató
├── jovokep-es-fejlesztesi-terv.md  # Roadmap és fejlesztési terv
├── karbantartas-utmutato.md   # Karbantartási eljárások
└── telepitesi-utmutato.md     # Telepítés (lokális, staging, éles)
```

### Melyik dokumentumot szerkesszem?

| Kérdés | Dokumentum |
|--------|-----------|
| Hogyan fut az alkalmazás? Mi kommunikál mivel? | `architektura.md` |
| Hogyan telepítem lokálisan / VPS-en? | `telepitesi-utmutato.md` |
| Hogyan írok backend kódot? | `backend-fejlesztes.md` |
| Hogyan írok frontend kódot? | `frontend-fejlesztes.md` |
| Docker, VS Code, Makefile, CI/CD kérdések? | `fejlesztoi-utmutato.md` |
| Hogyan működik a UI a felhasználó szemszögéből? | `felhasznaloi-utmutato.md` |
| Hogyan dokumentáljam a kódomat? | `dokumentacios-utmutato.md` |
| Hogyan tartom karban a prod rendszert? | `karbantartas-utmutato.md` |
| Mi a tervünk a jövőre? | `jovokep-es-fejlesztesi-terv.md` |

### Új dokumentum létrehozása

Ha teljesen új téma kerül a projektbe (pl. egy új integráció), amelyik nem fér bele a meglévő fájlokba:

1. Hozz létre egy fájlt a `docs/` mappában: `docs/uj-tema.md`
2. Add hozzá a navigációs sávot (lásd [7. szekció](#7-navigációs-sáv-karbantartása))
3. Frissítsd a `README.md` dokumentáció táblázatát
4. Frissítsd az összes többi dokumentum navigációs sávját

---

## 6. Markdown konvenciók

### Általános szabályok

| Szabály | Példa |
|---------|-------|
| H1 cím: 1 db per fájl, a fájl tetején | `# OpenSchool — Témakör` |
| H2 cím: fő szekciók, sorszámozva | `## 3. Fejezet címe` |
| H3 cím: alszekciók | `### Almappa szerkezet` |
| Kódblokkok: nyelv megadásával | ` ```python ... ``` ` |
| Táblázatok: fejléc + szeparátor + sorok | `| Oszlop | ... |` |
| Linkek: relatív útvonalak | `[szöveg](masik-fajl.md)` |
| Kiemelt megjegyzés | `> **Megjegyzés:** szöveg` |

### Link konvenciók

```markdown
# Ugyanabban a mappában lévő doc
[Backend útmutató](backend-fejlesztes.md)

# Szülő mappából (CONTRIBUTING.md → docs/)
[Backend útmutató](docs/backend-fejlesztes.md)

# Docs mappából a gyökérbe
[README](../README.md)

# Szekció hivatkozás (anchor)
[Lásd: 3. fejezet](fejlesztoi-utmutato.md#3-python-és-frontend-telepítés)
```

### Szekció anchor generálás

A Markdown automatikusan anchor-t generál a fejlécekből:

- Nagybetű → kisbetű
- Szóköz → kötőjel (`-`)
- Speciális karakterek (`(`, `)`, `.`, `,`) → törlődnek
- Ékezetek megmaradnak

Példa: `## 8. Változásnapló (git-cliff)` → `#8-változásnapló-git-cliff`

---

## 7. Navigációs sáv karbantartása

Minden dokumentum tetején van egy navigációs sáv a többi dokumentumra. Az aktuális oldal **félkövér** (link nélkül):

```markdown
> 📖 **Dokumentáció:** [Főoldal](../README.md) · [Architektúra](architektura.md) · ... · **Aktuális oldal** · ... · [Hozzájárulás](../CONTRIBUTING.md)
```

### Ha új dokumentumot adsz hozzá

1. Írd meg az új dokumentum navigációs sávját (az aktuális oldal félkövér)
2. Frissítsd az **összes többi dokumentum** navigációs sávját az új linkkel
3. Ügyelj arra, hogy a `CONTRIBUTING.md` és `README.md` eltérő relatív útvonalakat használ (`docs/...` prefix)

### Navigációs sáv sorrend

```
Főoldal · Architektúra · Telepítés · Fejlesztői útmutató · Backend · Frontend ·
Roadmap · Felhasználói útmutató · GitHub Classroom · Karbantartás · Automatizálás ·
Discord · Dokumentálás · Hozzájárulás
```

---

## 8. Változásnapló (CHANGELOG)

A `CHANGELOG.md` automatikusan generálódik a `git-cliff` eszközzel a konvencionális commit üzenetekből.

### Commit prefix → changelog szekció

| Prefix | Changelog szekció |
|--------|------------------|
| `feat:` | 🚀 Features |
| `fix:` | 🐛 Bug Fixes |
| `docs:` | 📚 Documentation |
| `refactor:` | 🚜 Refactor |
| `test:` | 🧪 Testing |
| `perf:` | ⚡ Performance |
| `chore:` / `ci:` | ⚙️ Miscellaneous Tasks |
| `security:` | 🛡️ Security |

### Changelog generálása

```bash
# Előnézet a terminálban
git cliff

# CHANGELOG.md felülírása
git cliff -o CHANGELOG.md

# Legutóbbi tag óta
git cliff --latest
```

Részletek: [Fejlesztői útmutató — 8. Változásnapló](fejlesztoi-utmutato.md#8-változásnapló-git-cliff)

---

## 9. README.md karbantartása

A `README.md` a projekt belépési pontja. Tartalmazza:

- Projekt leírás és filozófia
- Gyors indítás (`make dev-setup`)
- Technológiai verem
- API végpontok teljes táblázata
- Makefile parancsok
- Dokumentáció index

### Mikor kell frissíteni?

| Változás | README szekció |
|----------|----------------|
| Új API végpont | API végpontok tábla |
| Új Makefile target | Makefile parancsok tábla |
| Új dokumentum a `docs/`-ban | Dokumentáció tábla |
| Új technológia a stackben | Technológiai verem |

---

## 10. Ellenőrzőlista (PR előtt)

Mentsd el ezt a listát, és futtasd végig minden PR előtt:

- [ ] Új publikus függvényeknek van docstring-jük?
- [ ] Új API végpont megjelenik a Swagger-ben (docstring + summary)?
- [ ] A `README.md` API táblázata frissítve van?
- [ ] A `docs/` mappában az érintett dokumentumok frissítve vannak?
- [ ] Ha új dokumentum született, az összes navigációs sáv frissítve van?
- [ ] A `.env.example` tartalmazza az új környezeti változókat?
- [ ] A commit üzenetek konvencionális formátumot követnek?
- [ ] A `CHANGELOG.md` generálható hibátlanul (`git cliff`)?

---

> **Kapcsolódó dokumentáció:**
> - [Fejlesztői útmutató](fejlesztoi-utmutato.md) — Közös fejlesztői környezet, CI/CD
> - [Backend fejlesztés](backend-fejlesztes.md) — Python/FastAPI specifikus fejlesztés
> - [Frontend fejlesztés](frontend-fejlesztes.md) — Astro/JS specifikus fejlesztés
> - [Hozzájárulás](../CONTRIBUTING.md) — PR folyamat, kódstílus
