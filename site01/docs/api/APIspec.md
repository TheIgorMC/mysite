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
| `invite_raw`               | text       | Raw HTML invite content    |

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

### **ELEC_components**

| Column              | Type          | Description                          |
| ------------------- | ------------- | ------------------------------------ |
| `id`                | int           | Primary key                          |
| `seller`            | varchar(64)   | Seller/distributor name (e.g. LCSC)  |
| `seller_code`       | varchar(64)   | Seller's part number                 |
| `manufacturer`      | varchar(128)  | Manufacturer name                    |
| `manufacturer_code` | varchar(128)  | Manufacturer part number (MPN)       |
| `smd_footprint`     | varchar(32)   | SMD footprint (e.g. RESC1005)        |
| `package`           | varchar(32)   | Package size (e.g. 0402, 0603)       |
| `product_type`      | varchar(64)   | Component type (Resistor, Capacitor) |
| `value`             | varchar(64)   | Component value (e.g. 10k, 100nF)    |
| `price`             | decimal(10,4) | Unit price                           |
| `qty_left`          | int           | Available quantity in stock          |

---

### **mail_queue**

| Column            | Type         | Description                                  |
| ----------------- | ------------ | -------------------------------------------- |
| `id`              | int          | Primary key (auto-increment)                 |
| `recipient_email` | varchar(255) | Email address to send to                     |
| `mail_type`       | varchar(50)  | Email template type (welcome, invite, etc.)  |
| `locale`          | varchar(5)   | Language code ('it' or 'en')                 |
| `subject`         | varchar(255) | Custom subject (NULL = use template)         |
| `body_text`       | text         | Custom body text (NULL = use template)       |
| `details_json`    | json         | Key-value pairs for details table            |
| `status`          | enum         | 'pending', 'sent', or 'error'                |
| `scheduled_time`  | datetime     | When to send the email                       |
| `sent_at`         | datetime     | When email was sent (auto-filled)            |
| `error_message`   | text         | Error details if sending failed              |
| `created_at`      | datetime     | Record creation timestamp                    |
| `updated_at`      | datetime     | Last update timestamp                        |

---

### **ELEC_* tables** (for electronics inventory)

| Table                              | Purpose                               |
| ---------------------------------- | ------------------------------------- |
| `ELEC_boards`                      | Boards info (name, version, quantity) |
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

#### `GET /api/inviti/{codice}/text`

Get full invite details including raw HTML text for a specific competition.

**Path params:**

| Param    | Type   | Description             |
| -------- | ------ | ----------------------- |
| `codice` | string | Competition invite code |

**Response:**

```json
{
  "codice": "25A001",
  "solo_giovanile": 0,
  "numero_turni": 2,
  "data_apertura_iscrizioni": "2025-10-01",
  "data_chiusura_iscrizioni": "2025-10-25",
  "invite_raw": "<h1>Campionato Indoor 2025</h1><p>Details...</p>"
}
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

#### `GET /api/ranking/official`

Returns official FITARCO ranking from the cached ranking table (`MAT_ranking_cache`).

**Data Source:** `MAT_ranking_cache` table - contains scraped official rankings from the Fitarco website

**Sorting Criteria:**
1. Official Rank (Ascending) - as scraped from Fitarco
2. Total Score (Descending) - as tiebreaker

**Required Query Parameters:**

| Param        | Type   | Description                                                    |
| ------------ | ------ | -------------------------------------------------------------- |
| `code`       | string | Qualification code from `ARC_qualifiche` (e.g., "RegionaleIndoor2026Veneto") |
| `class_name` | string | Exact class name (e.g., "Senior Maschile", "Junior Femminile") |
| `division`   | string | Division/category (e.g., "Compound", "Arco Nudo") - supports partial match |

**Response:**

```json
[
  {
    "posizione": 1,
    "tessera": "012345",
    "atleta": "Zorzi Alberto",
    "societa": "Arcieri Treviso",
    "punteggio1": 285,
    "punteggio2": 283,
    "punteggio3": null,
    "punteggio4": null,
    "totale": 568,
    "data_qualificazione": "2025-11-15",
    "data_aggiornamento": "2025-12-10T15:30:00"
  },
  {
    "posizione": 2,
    "tessera": "067890",
    "atleta": "Rossi Mario",
    "societa": "Arcieri Marca",
    "punteggio1": 282,
    "punteggio2": 284,
    "punteggio3": null,
    "punteggio4": null,
    "totale": 566,
    "data_qualificazione": "2025-11-10",
    "data_aggiornamento": "2025-12-10T15:30:00"
  }
]
```

**Notes:**
- Position (`rank`) is the **official rank scraped from Fitarco website** - NOT recalculated
- Supports up to 4 scores (useful for Outdoor competitions: `punteggio1`, `punteggio2`, `punteggio3`, `punteggio4`)
- `data_qualificazione` shows the date when the qualification result was achieved
- `data_aggiornamento` shows when the cache was last updated from Fitarco
- Results are ordered by official rank first, then by total score
- Division parameter supports partial matching with wildcards (e.g., "Compound" matches "Arco Compound")
- Data comes from `MAT_ranking_cache` table which is periodically updated by scraping the official Fitarco rankings

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

Remove or cancel a registration. Behavior depends on current status:

- **Status = 'in attesa' / 'waiting' / 'pending'**: Deletes immediately from database
- **Status = 'confermato' / 'confirmed'**: Changes status to 'cancellation_requested' (does not delete)
- **Status = 'cancellation_confirmed'**: Deletes from database (allows new registration)
- **Other statuses**: Deletes immediately

**Response examples:**

Immediate deletion (waiting status):
```json
{"id": 182, "status": "deleted", "action": "immediate_deletion"}
```

Cancellation request (confirmed status):
```json
{"id": 182, "status": "cancellation_requested", "action": "cancellation_request"}
```

Confirmed cancellation deletion:
```json
{"id": 182, "status": "deleted", "action": "confirmed_deletion"}
```

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
    "id": 1,
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

## 📬 Mail Queue (Email Sending)

### `POST /api/mail/send`

Queue an email for sending. The mailer service picks up emails from the queue and sends them automatically.

**Body:**

```json
{
  "recipient_email": "user@example.com",
  "mail_type": "invite",
  "locale": "it",
  "subject": "Invito alla Gara R2506017",
  "body_text": "La gara è ora disponibile per le iscrizioni!",
  "details_json": {
    "Codice Gara": "R2506017",
    "Nome Gara": "Campionato Regionale",
    "Data": "2025-06-14",
    "Luogo": "Firenze"
  },
  "scheduled_time": "2025-12-01T09:00:00"
}
```

**Fields:**

| Field              | Type   | Required | Default | Description                                      |
| ------------------ | ------ | -------- | ------- | ------------------------------------------------ |
| `recipient_email`  | string | ✅ Yes   | -       | Email address to send to                         |
| `mail_type`        | string | ✅ Yes   | -       | Template type (see below)                        |
| `locale`           | string | No       | `"it"`  | Language: `"it"` or `"en"`                       |
| `subject`          | string | No       | `null`  | Custom subject (null = use template default)     |
| `body_text`        | string | No       | `null`  | Custom body text (null = use template default)   |
| `details_json`     | object | No       | `null`  | Key-value pairs displayed as table in email      |
| `scheduled_time`   | string | No       | `null`  | ISO datetime (null = send immediately with NOW())|

**Valid mail_type values:**

- `welcome` - Welcome email
- `access` - Access granted
- `interest` - Interest registered
- `invite` - Invite published
- `subscription` - Subscription received
- `modification` - Modification requested
- `modification_confirmed` - Modification done
- `cancellation` - Cancellation requested
- `cancellation_confirmed` - Cancellation done
- `closing_soon` - Closing warning
- `opening_soon` - Opening notice

**Response:**

```json
{
  "id": 123,
  "status": "queued",
  "message": "Email queued successfully. Mailer will process it shortly."
}
```

**Examples:**

Simple email (immediate, using template defaults):
```json
{
  "recipient_email": "user@example.com",
  "mail_type": "welcome"
}
```

Email with custom text and details:
```json
{
  "recipient_email": "athlete@example.com",
  "mail_type": "subscription",
  "body_text": "La tua iscrizione è stata confermata. Ecco i dettagli:",
  "details_json": {
    "Atleta": "Mario Rossi",
    "Tessera": "123456",
    "Gara": "R2506017",
    "Data": "2025-06-14",
    "Arco": "Olimpico"
  }
}
```

Scheduled email for future:
```json
{
  "recipient_email": "user@example.com",
  "mail_type": "closing_soon",
  "scheduled_time": "2025-12-23T09:00:00"
}
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
  ├── /api/mail/send → email queue management
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
Returns:
```json
[
  {
    "board_id": 5,
    "component_id": 123,
    "qty": 10,
    "designators": "R1,R2,R3",
    "product_type": "Resistor",
    "value": "10k",
    "package": "0402",
    "smd_footprint": "RESC1005",
    "manufacturer_code": "RC0402FR-0710KL",
    "qty_left": 5000
  }
]
```

**POST `/api/elec/boards/{id}/bom`** – add/update items
Body:

```json
[
  {"component_id": 123, "qty": 10, "designators": "R1,R2,R3"},
  {"component_id": 456, "qty": 2, "designators": "C1,C2"}
]
```

Notes:
- `designators` is optional, can contain comma-separated component references
- If `designators` is provided, it will be stored in the database
- Used for OpenPnP export to map physical component locations to component IDs

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

### Files Table Structure
Database table: `ELEC_board_files` **(Already Implemented)**

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Primary key (auto-increment) |
| `board_id` | int | FK → `ELEC_boards.id` |
| `file_type` | varchar(50) | Type: gerber, schematic, bom, pnp, datasheet, pcb_layout, ibom, documentation, firmware, cad |
| `filename` | varchar(255) | Original filename |
| `file_path` | varchar(500) | URL or storage path |
| `file_size` | int | Size in bytes |
| `mime_type` | varchar(100) | MIME type |
| `uploaded_by` | varchar(100) | User who uploaded |
| `uploaded_at` | datetime | Upload timestamp |
| `version_tag` | varchar(50) | Optional version label |
| `notes` | text | Optional notes |

### Endpoints **(Already Implemented)**

**GET `/api/elec/boards/{board_id}/files`** – list files for a specific board
Returns:
```json
[
  {
    "id": 1,
    "board_id": 5,
    "file_type": "gerber",
    "filename": "mainboard_v1.2_gerbers.zip",
    "file_path": "/storage/boards/5/gerbers/mainboard_v1.2.zip",
    "file_size": 524288,
    "mime_type": "application/zip",
    "uploaded_by": "admin",
    "uploaded_at": "2025-11-18T10:30:00",
    "version_tag": "v1.2",
    "notes": "JLC job #2025-001"
  }
]
```

**POST `/api/elec/boards/{board_id}/files`** – register/upload file metadata
Body:
```json
{
  "file_type": "gerber",
  "filename": "controller_v1.2_gerbers.zip",
  "file_path": "/storage/boards/5/gerbers/controller_v1.2.zip",
  "file_size": 524288,
  "mime_type": "application/zip",
  "uploaded_by": "admin",
  "version_tag": "v1.2",
  "notes": "JLC job #2025-001"
}
```
Returns: `{"id": 1, "status": "created"}`

**DELETE `/api/elec/boards/{board_id}/files/{file_id}`** – delete file metadata
Returns: `{"id": 1, "status": "deleted"}`

**GET `/api/elec/files/{file_id}/download`** – download a file
Returns: File download with appropriate Content-Type header

---

## 🤖 Pick & Place (PnP) File Management

### PnP Table Structure
Database table: `ELEC_pnp`

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Primary key (auto-increment) |
| `board_id` | int | FK → `ELEC_boards.id` |
| `filename` | varchar(255) | PnP file name |
| `created_at` | datetime | Upload timestamp |
| `component_count` | int | Total components in file |

### PnP Data Table Structure
Database table: `ELEC_pnp_data`

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Primary key (auto-increment) |
| `pnp_id` | int | FK → `ELEC_pnp.id` |
| `designator` | varchar(50) | Component reference (e.g., "U1", "R5") |
| `mid_x` | varchar(20) | Center X coordinate with unit (e.g., "57.15mm") |
| `mid_y` | varchar(20) | Center Y coordinate with unit |
| `ref_x` | varchar(20) | Reference X coordinate (optional) |
| `ref_y` | varchar(20) | Reference Y coordinate (optional) |
| `pad_x` | varchar(20) | Pad X coordinate (optional) |
| `pad_y` | varchar(20) | Pad Y coordinate (optional) |
| `layer` | varchar(10) | PCB layer: "T" or "Top" for top, "B" or "Bottom" for bottom |
| `rotation` | varchar(10) | Rotation angle in degrees (e.g., "0", "90", "180") |
| `comment` | varchar(255) | Component value/description |
| `device` | varchar(255) | Device/part name |

### Endpoints

**GET `/api/elec/pnp`** – list all PnP files
Query params: `board_id`, `limit`, `offset`
Returns:
```json
[
  {
    "id": 1,
    "board_id": 5,
    "board_name": "Mainboard",
    "board_version": "v1.2",
    "filename": "Mainboard_V1.2_PnP",
    "created_at": "2025-11-18T10:30:00",
    "component_count": 150
  }
]
```

**POST `/api/elec/pnp`** – upload new PnP file
Body:
```json
{
  "board_id": 5,
  "filename": "Mainboard_V1.2_PnP",
  "csv_data": "Designator,Mid X,Mid Y,Ref X,Ref Y,Pad X,Pad Y,Layer,Rotation,Comment,Device\n\"U1\",\"57.15mm\",\"68.834mm\",\"57.15mm\",\"68.834mm\",\"65.9mm\",\"79.634mm\",\"T\",\"180\",\"STM32F407ZGT6\",\"STM32F407ZGT6\"\n..."
}
```

**CSV Parsing Logic:**
- Parse CSV with headers (first line)
- Required columns: `Designator`, `Mid X`, `Mid Y`, `Layer`, `Rotation`
- Optional columns: `Ref X`, `Ref Y`, `Pad X`, `Pad Y`, `Comment`, `Device`
- Strip quotes from values
- Store coordinate values as-is (including "mm" suffix if present)
- Count total components for `component_count`
- Create one `ELEC_pnp` record and multiple `ELEC_pnp_data` records

Returns: `{"id": 1, "status": "created", "component_count": 150}`

**GET `/api/elec/pnp/{id}`** – get PnP file with full data
Returns:
```json
{
  "id": 1,
  "board_id": 5,
  "board_name": "Mainboard",
  "board_version": "v1.2",
  "filename": "Mainboard_V1.2_PnP",
  "created_at": "2025-11-18T10:30:00",
  "component_count": 150,
  "pnp_data": [
    {
      "id": 1,
      "designator": "U1",
      "mid_x": "57.15mm",
      "mid_y": "68.834mm",
      "ref_x": "57.15mm",
      "ref_y": "68.834mm",
      "pad_x": "65.9mm",
      "pad_y": "79.634mm",
      "layer": "T",
      "rotation": "180",
      "comment": "STM32F407ZGT6",
      "device": "STM32F407ZGT6"
    },
    ...
  ]
}
```

**DELETE `/api/elec/pnp/{id}`** – delete PnP file and all associated data
- Deletes from `ELEC_pnp_data` where `pnp_id = {id}`
- Deletes from `ELEC_pnp` where `id = {id}`
Returns: `{"id": 1, "status": "deleted"}`

**GET `/api/elec/boards/{board_id}/pnp`** – list PnP files for specific board
Returns array like GET `/api/elec/pnp?board_id={board_id}`

---

## 🧠 Notes

* IDs for ELEC entities are nulls as the DB has them on Autoincrement
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