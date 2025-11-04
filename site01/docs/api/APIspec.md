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

**Params:**

| Param          | Type   | Description                      |
| -------------- | ------ | -------------------------------- |
| `q`            | string | Search query (optional)          |
| `product_type` | string | Filter by product type (optional)|
| `package`      | string | Filter by package (optional)     |
| `limit`        | int    | Max results (default: 100)       |
| `offset`       | int    | Pagination offset (default: 0)   |

**Response:**

```json
[
  {
    "id": "COMP001",
    "seller": "LCSC",
    "seller_code": "C25804",
    "manufacturer": "Yageo",
    "manufacturer_code": "RC0402FR-0710KL",
    "smd_footprint": "RESC1005",
    "package": "0402",
    "product_type": "Resistor",
    "value": "10k",
    "price": 0.0025,
    "qty_left": 5000
  }
]
```

---

## 💬 Interesse (Expressions of Interest)

### `GET /api/interesse`

Retrieve interest expressions.

**Params:**

| Param            | Type   | Description                        |
| ---------------- | ------ | ---------------------------------- |
| `tessera_atleta` | string | Filter by athlete ID               |
| `codice_gara`    | string | Filter by competition code (admin) |

**Response:**

```json
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
```

---

### `POST /api/interesse`

Create a new interest expression.

**Body:**

```json
{
  "codice_gara": "25A001",
  "tessera_atleta": "012345",
  "categoria": "CO",
  "classe": "Senior",
  "data_interesse": "2025-10-15",
  "note": "Preferenza per il turno mattina",
  "stato": "attivo"
}
```

**Response:**

```json
{"id": 4, "status": "created"}
```

---

### `DELETE /api/interesse/{id}`

Delete an interest expression (by ID).

**Response:**

```json
{"id": 4, "status": "deleted"}
```

---

## 🧱 Data Flow Update

```text
Frontend → FastAPI → MySQL (orion_db)

Modules:
  ├── /api/atleti, /api/societa → read-only lists
  ├── /api/gare, /api/turni, /api/inviti → event and invite info
  ├── /api/interesse → interest tracking (pre-registration)
  ├── /api/iscrizioni → full CRUD + export
  ├── /api/stats, /api/ranking → analytics
  └── /api/elec/... → electronics management
```

---

### 🧾 Athlete Results

#### `GET /api/athlete/{tessera}/results`

Return detailed competition results for an athlete, with optional filters and a quick summary (best score, averages).

**Path params**

* `tessera` (string, required): Athlete ID

**Query params**

| Param        | Type                | Description                                         |
| ------------ | ------------------- | --------------------------------------------------- |
| `event_type` | string              | Filter by competition type (e.g. `Indoor`, `Targa`) |
| `from_date`  | date (`YYYY-MM-DD`) | Include results from this date                      |
| `to_date`    | date (`YYYY-MM-DD`) | Include results up to this date                     |
| `limit`      | int                 | Max results (default **500**)                       |

**Response**

```json
{
  "summary": {
    "count": 3,
    "best_score": 562,
    "avg_score": 548.33,
    "avg_position": 4.67
  },
  "results": [
    {
      "tessera": "012345",
      "atleta": "Zorzi Alberto",
      "codice_societa_atleta": "06/006",
      "nome_societa_atleta": "Arcieri Treviso",
      "nome_gara": "Campionato Indoor",
      "tipo_gara": "Indoor",
      "data_gara": "2025-02-14",
      "codice_gara": "25A001",
      "luogo_gara": "Treviso",
      "codice_societa_organizzatrice": "06/010",
      "nome_societa_organizzatrice": "Arcieri Marca",
      "posizione": 3,
      "punteggio": 558
    }
  ]
}
```

**Notes**

* `avg_position` is computed only over results with a defined `posizione`.
* `best_score`/`avg_score` use `punteggio` (`r.punteggio_tot` in DB).
* Results are ordered by most recent (`data_inizio DESC`).
* **best_score logic:**

  * For events whose **name** contains `25+18` or `doppio` (case-insensitive), the **highest score** is computed over the **individual partials** (`part1`, `part2`, `part3`) when available; otherwise it falls back to the total.
  * For all other events, `best_score` uses `punteggio_tot` (total).
* **Averages unchanged:** `avg_score` still averages `punteggio_tot`; `avg_position` averages final positions.

---

## 🔧 Electronics Components Management

**GET `/api/elec/components`** – list components
Params: `q`, `product_type`, `package`, `limit`, `offset`

**POST `/api/elec/components`** – create component
Body:

```json
{
  "seller": "LCSC",
  "seller_code": "C25804",
  "manufacturer": "Yageo",
  "manufacturer_code": "RC0402FR-0710KL",
  "smd_footprint": "RESC1005",
  "package": "0402",
  "product_type": "Resistor",
  "value": "10k",
  "price": 0.0025,
  "qty_left": 5000
}
```

**PATCH `/api/elec/components/{id}`** – update fields (e.g. `qty_left`)
**DELETE `/api/elec/components/{id}`** – delete

**GET `/api/elec/components/search?q=R0402`** – smart search

* `R0402` → product_type like `Resistor%`, package `0402`
* Else: fuzzy on manufacturer, value, package, product_type…

---

## 🪛 Boards Management

**GET `/api/elec/boards`** – list
**POST `/api/elec/boards`** – create
**PATCH `/api/elec/boards/{id}`** – update
**DELETE `/api/elec/boards/{id}`** – delete

**POST `/api/elec/boards/{id}/upload_bom`** – upload BOM CSV

* CSV must contain columns: `component_id,qty`
* Upserts into `ELEC_board_components`

---

## 📦 Board–Component Relations (BOM)

**GET `/api/elec/boards/{id}/bom`** – return BOM (with component info)
**POST `/api/elec/boards/{id}/bom`** – add/update items
Body:

```json
[
  {"component_id":"abc123...", "qty": 10},
  {"component_id":"def456...", "qty": 2}
]
```

**DELETE `/api/elec/boards/{id}/bom/{comp_id}`** – remove component from BOM

---

## 🏭 Production Jobs

**GET `/api/elec/jobs`** – list jobs
**POST `/api/elec/jobs`** – create job
Body:

```json
{
  "board_id": "board123...",
  "quantity": 10,
  "pnp_job": 1,
  "status": "created",
  "due_date": "2025-11-15"
}
```

**GET `/api/elec/jobs/{id}`** – job details (includes BOM)
**PATCH `/api/elec/jobs/{id}`** – update status/qty/due_date
**GET `/api/elec/jobs/{id}/check_stock`** – availability vs. BOM×quantity
**POST `/api/elec/jobs/{id}/reserve_stock`** – atomically decrement `qty_left`
*409 if any component is insufficient.*

**GET `/api/elec/jobs/{id}/missing_bom`** – list missing components

---

## ⬇️ Export

**GET `/api/elec/bom/export?format=csv&job_id={id}`**
OR `?board_id={id}&qty=XX`
→ Streams a CSV of the required components and quantities.

---

## 📁 File Storage Management

**GET `/api/elec/boards/{id}/files`** – list files for a board
**POST `/api/elec/boards/{id}/files`** – register/upload metadata
Body:

```json
{
  "file_type": "gerber",
  "filename": "controller_v1.2_gerbers.zip",
  "file_path": "https://files.example.com/elec/boards/123/gerbers.zip",
  "file_size": 524288,
  "mime_type": "application/zip",
  "uploaded_by": "admin",
  "version_tag": "v1.2",
  "notes": "JLC job #2025-001"
}
```

**DELETE `/api/elec/boards/{id}/files/{file_id}`** – delete file metadata
**GET `/api/elec/files/{id}/download`** – HTTP 302 redirect to `file_path`
**GET `/api/elec/files/types`** – supported `file_type` list

---

## 🧠 Notes

* IDs for ELEC entities are generated as 32-hex strings if not provided.
* Stock reservation uses **transaction + row locks** to be safe under concurrency.
* BOM CSV kept intentionally minimal (`component_id, qty`); expand later if you want fuzzy mapping by `manufacturer_code + package + value`.
* For large exports, consider paging or streaming on the frontend.

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