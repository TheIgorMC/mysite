# 🏹 ORION / Archery API — Documentation

Version: **2.4**
Database: **`orion_db`** (MariaDB/MySQL)
Framework: **FastAPI**
Auth: *(currently open, optional Bearer auth can be added)*

---

## 🧩 DATABASE STRUCTURE OVERVIEW

### **ARC_atleti**

| Column           | Type         | Description                  |
| ---------------- | ------------ | ---------------------------- |
| `tessera`        | varchar(10)  | Primary key (athlete ID)     |
| `nome`           | varchar(100) | Athlete name                 |
| `classe`         | varchar(5)   | Category/class (e.g. CO, OL) |
| `societa_codice` | varchar(10)  | FK → `ARC_societa.codice`    |

---

### **ARC_societa**

| Column        | Type         | Description            |
| ------------- | ------------ | ---------------------- |
| `codice`      | varchar(10)  | Primary key            |
| `nome`        | varchar(255) | Club name              |
| `provincia`   | varchar(10)  | Province               |
| `regione`     | varchar(50)  | Region                 |
| `lat` / `lon` | decimal(9,6) | Geographic coordinates |

---

### **ARC_gare**

| Column                      | Type         | Description                     |
| --------------------------- | ------------ | ------------------------------- |
| `id`                        | int          | Primary key                     |
| `codice`                    | varchar(20)  | Event code                      |
| `nome`                      | varchar(255) | Event name                      |
| `tipo`                      | varchar(100) | Event type (e.g. Indoor, Targa) |
| `societa_codice`            | varchar(10)  | Organizing society              |
| `luogo`                     | varchar(255) | Event location (city or venue)  |
| `data_inizio` / `data_fine` | date         | Start / end date                |

---

### **ARC_inviti**

| Column                     | Type       | Description                |
| -------------------------- | ---------- | -------------------------- |
| `codice`                   | varchar(8) | Primary key                |
| `solo_giovanile`           | tinyint(1) | Youth-only flag (1 = yes)  |
| `numero_turni`             | int        | Number of available rounds |
| `data_apertura_iscrizioni` | date       | Registration opening date  |
| `data_chiusura_iscrizioni` | date       | Registration closing date  |

---

### **ARC_risultati**

| Column                    | Type         | Description               |
| ------------------------- | ------------ | ------------------------- |
| `id`                      | int          | Primary key               |
| `gara_id`                 | int          | FK → `ARC_gare.id`        |
| `tessera`                 | varchar(10)  | FK → `ARC_atleti.tessera` |
| `nome_completo`           | varchar(200) | Athlete full name         |
| `categoria`               | varchar(32)  | Division                  |
| `classe_gara`             | varchar(32)  | Class (Senior, Junior...) |
| `posizione`               | int          | Final position            |
| `punteggio_tot`           | int          | Total score               |
| `part1`, `part2`, `part3` | int          | Partial scores            |

---

### **ARC_iscrizioni**

| Column           | Type        | Description               |
| ---------------- | ----------- | ------------------------- |
| `id`             | bigint      | Primary key               |
| `codice_gara`    | varchar(8)  | FK → `ARC_gare.codice`    |
| `tessera_atleta` | varchar(10) | FK → `ARC_atleti.tessera` |
| `categoria`      | varchar(10) | Category (optional)       |
| `classe`         | varchar(20) | Class (optional)          |
| `turno`          | int         | Round number              |
| `stato`          | varchar(20) | Registration status       |
| `note`           | text        | Optional notes            |

---

### **ARC_turni**

| Column            | Type        | Description                          |
| ----------------- | ----------- | ------------------------------------ |
| `id`              | int         | Primary key                          |
| `codice_gara`     | varchar(8)  | FK → `ARC_gare.codice`               |
| `turno`           | int         | Turn number                          |
| `giorno`          | varchar(20) | Day descriptor                       |
| `fase`            | varchar(20) | Phase (e.g. Qualifica, Eliminatoria) |
| `ora_ritrovo`     | time        | Call time                            |
| `ora_inizio_tiri` | time        | Start time                           |

---

### **ARC_qualifiche**

| Column                      | Type         | Description    |
| --------------------------- | ------------ | -------------- |
| `codice`                    | varchar(50)  | Code           |
| `descrizione`               | varchar(255) | Description    |
| `data_inizio` / `data_fine` | date         | Period covered |
| `regione`                   | varchar(50)  | Region         |

---

### **ELEC_* tables** (for electronics inventory)

| Table                              | Purpose                               |
| ---------------------------------- | ------------------------------------- |
| `ELEC_boards`                      | Boards info (name, version, quantity) |
| `ELEC_components`                  | Electronic components list            |
| `ELEC_board_components`            | Board–component relation              |
| `ELEC_orders` / `ELEC_order_items` | Purchase orders                       |
| `ELEC_jobs`                        | Production jobs                       |

---

## ⚙️ API STRUCTURE

### 🔍 Service & Metadata

#### `GET /api/ping`

Health check.
**Response:**

```json
{"status": "ok", "message": "Archery API running"}
```

#### `GET /api/event_types`

Returns distinct event types.
**Response:**
`["Indoor", "Targa", "Campagna"]`

---

### 🧑‍🤝‍🧑 Società & Atleti

#### `GET /api/societa?include_coords=true`

List all societies (optionally with lat/lon).

#### `GET /api/atleti?q=zorzi&limit=20`

Search athletes by name.

---

### 🏹 Gare (Events)

#### `GET /api/gare?future=true`

List upcoming or recent events.

**Params:**

* `future` (bool) — default false
* `limit` (int) — default 20

**Response:**

```json
[
  {
    "codice": "25A001",
    "nome": "Campionato Indoor",
    "tipo": "Indoor",
    "societa_codice": "06/006",
    "luogo": "Treviso",
    "data_inizio": "2025-11-02",
    "data_fine": "2025-11-03"
  }
]
```

---

#### `GET /api/turni?codice_gara=25A001`

Returns turn schedule for given event.

---

### 📩 Inviti (Invitations)

#### `GET /api/inviti`

List competition invitations.

**Params:**

| Param        | Type   | Description                                    |
| ------------ | ------ | ---------------------------------------------- |
| `codice`     | string | filter by specific code                        |
| `only_open`  | bool   | show only currently open registrations         |
| `only_youth` | bool   | show only youth competitions                   |
| `export`     | string | if `"full"`, returns all invites (mass export) |

**Response:**

```json
[
  {
    "codice": "25A001",
    "solo_giovanile": 0,
    "numero_turni": 2,
    "data_apertura_iscrizioni": "2025-10-01",
    "data_chiusura_iscrizioni": "2025-10-25"
  }
]
```

---

### 🏁 Qualifiche

#### `GET /api/qualifiche`

List qualification periods (for ranking filters).

---

### 📊 Statistics

#### `GET /api/stats`

Get performance timeline for a list of athletes.

**Params:**

* `athletes`: list of tessera IDs
* `event_type`, `from_date`, `to_date`, `period_months`

**Response:**

```json
{
  "labels": ["2024-03-05", "2024-05-20"],
  "datasets": [
    {"label": "012345", "data": [524, 531]}
  ]
}
```

---

#### `GET /api/best?athlete=012345&event_type=Indoor`

Highest score achieved by an athlete.

---

#### `GET /api/ranking?event_type=Indoor&region=Veneto`

Average rankings for a given type/region.

---

### 🧾 Iscrizioni (Registrations)

#### `GET /api/iscrizioni`

List registrations for an event or athlete.
Supports **mass export** with `export=full`.

**Params:**

| Param         | Type   | Description                                          |
| ------------- | ------ | ---------------------------------------------------- |
| `codice_gara` | string | filter by competition                                |
| `tessera`     | string | filter by athlete                                    |
| `export`      | string | if `"full"`, returns all registrations (mass export) |

**Response:**

```json
[
  {
    "id": 12,
    "codice_gara": "25A001",
    "nome_gara": "Campionato Indoor",
    "luogo_gara": "Treviso",
    "tessera_atleta": "012345",
    "nome_atleta": "Zorzi Alberto",
    "categoria": "CO",
    "classe": "Senior",
    "turno": 1,
    "stato": "confermato",
    "note": "Turno mattina"
  }
]
```

---

#### `POST /api/iscrizioni`

Create a new registration.

**Body:**

```json
{
  "codice_gara": "25A001",
  "tessera_atleta": "012345",
  "categoria": "CO",
  "classe": "Senior",
  "turno": 1,
  "stato": "confermato",
  "note": "Richiesta mattina"
}
```

**Response:**

```json
{"id": 182, "status": "created"}
```

---

#### `PATCH /api/iscrizioni/{id}`

Update an existing registration (status, note, turno, categoria, classe).

**Body:**

```json
{"stato": "ritirato", "note": "Infortunio"}
```

---

#### `DELETE /api/iscrizioni/{id}`

Remove a registration.
**Response:** `{"id": 182, "status": "deleted"}`

---

### 🔧 Electronics (optional subsystem)

#### `GET /api/elec/boards`

List electronic boards.

#### `GET /api/elec/components?limit=50`

List available components.

---

## 🧱 DATA FLOW OVERVIEW

```text
Frontend → FastAPI → MySQL (orion_db)

Modules:
  ├── /api/atleti, /api/societa → read-only lists
  ├── /api/gare, /api/turni, /api/inviti → events info
  ├── /api/iscrizioni → full CRUD + export
  ├── /api/stats, /api/ranking → analytical charts
  └── /api/elec/... → hardware management
```

---

## 🧠 Notes for Frontend Developers

* JSON format throughout
* Dates use `YYYY-MM-DD` (ISO 8601)
* CORS is fully open (`*`)
* Default port inside container: **80**
* Recommended request headers:

  ```http
  Content-Type: application/json
  Accept: application/json
  ```
