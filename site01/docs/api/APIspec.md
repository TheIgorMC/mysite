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

💬 Interesse (Expressions of Interest)
GET /api/interesse

Retrieve interest expressions.

Params:

Param	Type	Description
tessera_atleta	string	Filter by athlete ID
codice_gara	string	Filter by competition code (admin)

Response:

[
  {
    "id": 4,
    "codice_gara": "25A001",
    "nome_gara": "Campionato Indoor",
    "tessera_atleta": "012345",
    "nome_atleta": "Zorzi Alberto",
    "categoria": "CO",
    "classe": "Senior",
    "data_interesse": "2025-10-15",
    "note": "Preferenza per il turno mattina",
    "stato": "attivo"
  }
]

POST /api/interesse

Create a new interest expression.

Body:

{
  "codice_gara": "25A001",
  "tessera_atleta": "012345",
  "categoria": "CO",
  "classe": "Senior",
  "data_interesse": "2025-10-15",
  "note": "Preferenza per il turno mattina",
  "stato": "attivo"
}


Response:

{"id": 4, "status": "created"}

DELETE /api/interesse/{id}

Delete an interest expression (by ID).

Response:

{"id": 4, "status": "deleted"}

🧱 Data Flow Update
Frontend → FastAPI → MySQL (orion_db)

Modules:
  ├── /api/atleti, /api/societa → read-only lists
  ├── /api/gare, /api/turni, /api/inviti → event and invite info
  ├── /api/interesse → interest tracking (pre-registration)
  ├── /api/iscrizioni → full CRUD + export
  ├── /api/stats, /api/ranking → analytics
  └── /api/elec/... → electronics management

---

📦 Materiali (Stringmaking Stock)
GET /api/materiali

List materials with filters.

Query params

Param	Type	Description
q	string	Search in materiale/colore/spessore
tipo	string	Filter by type (string, serving, center, …)
low_stock_lt	number	Show only items with rimasto below threshold
limit	int	Default 100
offset	int	Default 0

Response

[
  {
    "id": 3,
    "materiale": "BCY 652",
    "colore": "Flo Green",
    "spessore": "0.021",
    "rimasto": 132.50,
    "costo": 0.18,
    "tipo": "string",
    "created_at": "2025-10-01T10:22:00",
    "updated_at": "2025-10-27T09:12:34"
  }
]

POST /api/materiali

Create a new material entry.

Body

{
  "materiale": "BCY X99",
  "colore": "Black",
  "spessore": "0.026",
  "rimasto": 250.00,
  "costo": 0.22,
  "tipo": "string"
}


Response

{"id": 7, "status": "created"}

PATCH /api/materiali/{id}

Update any field (partial update).

Body (example)

{
  "rimasto": 210.00,
  "costo": 0.21
}


Response

{"id": 7, "status": "updated"}

POST /api/materiali/{id}/consume

Consume a quantity from stock (atomic, non-negative).

Body

{
  "quantita": 12.50
}


Response

{"id": 7, "rimasto": "197.50", "status": "consumed"}


Errors:

409: stock insufficient (rimasto too low)

DELETE /api/materiali/{id}

Delete a material entry.

Response

{"id": 7, "status": "deleted"}

🔬 Suggested indexes (performance)
CREATE INDEX idx_mat_variant ON ARC_materiali (materiale, colore, spessore, tipo);
CREATE INDEX idx_mat_low ON ARC_materiali (rimasto);
CREATE INDEX idx_mat_tipo ON ARC_materiali (tipo);

---

## 🧠 Notes for Frontend Developers

* JSON format throughout
* Dates use `YYYY-MM-DD` (ISO 8601)
* CORS is fully open (`*`)
* Default port inside container: **80**
* Recommended request headers:

  ```http
  Content-Type: application/json
  Accept: application/json```