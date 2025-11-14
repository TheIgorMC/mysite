# 📬 Mail Queue Database Schema - Quick Reference

## Table: `mail_queue`

Quick guide for inserting emails from your API/scripts.

---

## 🎯 Quick Insert Examples

### Basic Email (Use Template Defaults)
```sql
INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time) 
VALUES ('user@example.com', 'welcome', 'it', NOW());
```

### Email with Custom Body
```sql
INSERT INTO mail_queue (recipient_email, mail_type, locale, body_text, scheduled_time) 
VALUES ('user@example.com', 'invite', 'it', 'La gara è disponibile!', NOW());
```

### Email with Details (JSON)
```sql
INSERT INTO mail_queue (
    recipient_email, 
    mail_type, 
    locale, 
    body_text,
    details_json,
    scheduled_time
) VALUES (
    'user@example.com', 
    'subscription', 
    'it',
    'Ecco i dettagli della tua iscrizione:',
    '{"Codice Gara": "R2506017", "Data": "2025-06-14", "Arco": "Olimpico"}',
    NOW()
);
```

### Scheduled for Later
```sql
INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time) 
VALUES ('user@example.com', 'closing_soon', 'it', '2025-12-25 09:00:00');
```

---

## 📋 Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | INT | Auto | - | Primary key (auto-increment) |
| `recipient_email` | VARCHAR(255) | ✅ Yes | - | Email address to send to |
| `mail_type` | VARCHAR(50) | ✅ Yes | - | Email template type (see below) |
| `locale` | VARCHAR(5) | No | `'it'` | Language: `'it'` or `'en'` |
| `subject` | VARCHAR(255) | No | NULL | Custom subject (NULL = use template) |
| `body_text` | TEXT | No | NULL | Custom body text (NULL = use template) |
| `details_json` | JSON | No | NULL | Key-value pairs for details table |
| `status` | ENUM | No | `'pending'` | `'pending'`, `'sent'`, or `'error'` |
| `scheduled_time` | DATETIME | ✅ Yes | - | When to send (use `NOW()` for immediate) |
| `sent_at` | DATETIME | No | NULL | Timestamp when sent (auto-filled) |
| `error_message` | TEXT | No | NULL | Error details (auto-filled) |
| `created_at` | DATETIME | Auto | NOW | Record creation time |
| `updated_at` | DATETIME | Auto | NOW | Last update time |

---

## 📧 Mail Types (mail_type)

| Value | Description | Use Case |
|-------|-------------|----------|
| `welcome` | Welcome email | After user registration |
| `access` | Access granted | Club members section access |
| `interest` | Interest registered | User expresses interest in competition |
| `invite` | Invite published | Competition invite with details |
| `subscription` | Subscription received | Registration request with recap |
| `modification` | Modification requested | User requests changes |
| `modification_confirmed` | Modification done | Changes completed |
| `cancellation` | Cancellation requested | User wants to cancel |
| `cancellation_confirmed` | Cancellation done | Cancellation completed |
| `closing_soon` | Closing warning | Subscriptions closing in 2 days |
| `opening_soon` | Opening notice | Subscriptions opening soon |

---

## 🗂️ Details JSON Format

The `details_json` field displays key-value pairs in a nice table in the email.

### Example JSON:
```json
{
    "Codice Gara": "R2506017",
    "Nome Gara": "Campionato Regionale",
    "Data": "2025-06-14",
    "Luogo": "Firenze",
    "Arco": "Olimpico",
    "Categoria": "Senior"
}
```

### In Email, Shows As:
```
┌────────────────┬──────────────────────────┐
│ Codice Gara    │ R2506017                 │
│ Nome Gara      │ Campionato Regionale     │
│ Data           │ 2025-06-14               │
│ Luogo          │ Firenze                  │
│ Arco           │ Olimpico                 │
│ Categoria      │ Senior                   │
└────────────────┴──────────────────────────┘
```

---

## 🔧 Common Patterns

### 1. Send Immediate Email
```sql
INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time) 
VALUES ('user@example.com', 'welcome', 'it', NOW());
```

### 2. Schedule Email for Future
```sql
INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time) 
VALUES ('user@example.com', 'closing_soon', 'it', DATE_ADD(NOW(), INTERVAL 2 DAY));
```

### 3. Batch Insert Multiple Recipients
```sql
INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time) VALUES
('user1@example.com', 'invite', 'it', NOW()),
('user2@example.com', 'invite', 'it', NOW()),
('user3@example.com', 'invite', 'it', NOW());
```

### 4. Email with All Custom Fields
```sql
INSERT INTO mail_queue (
    recipient_email,
    mail_type,
    locale,
    subject,
    body_text,
    details_json,
    scheduled_time
) VALUES (
    'user@example.com',
    'subscription',
    'it',
    'Conferma Iscrizione - Gara R2506017',
    'La tua iscrizione è stata confermata. Ecco i dettagli completi:',
    '{"Atleta": "Mario Rossi", "Tessera": "123456", "Gara": "R2506017", "Data": "2025-06-14"}',
    NOW()
);
```

---

## 🐍 Python/API Examples

### Using Python
```python
import mysql.connector
import json
from datetime import datetime

conn = mysql.connector.connect(
    host='your_db_host',
    user='your_db_user',
    password='your_db_password',
    database='orion'
)

cursor = conn.cursor()

# Simple email
cursor.execute("""
    INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time)
    VALUES (%s, %s, %s, %s)
""", ('user@example.com', 'welcome', 'it', datetime.now()))

# Email with details
details = {
    "Codice Gara": "R2506017",
    "Data": "2025-06-14",
    "Arco": "Olimpico"
}

cursor.execute("""
    INSERT INTO mail_queue (
        recipient_email, mail_type, locale, body_text, details_json, scheduled_time
    ) VALUES (%s, %s, %s, %s, %s, %s)
""", (
    'user@example.com',
    'invite',
    'it',
    'L\'invito è disponibile!',
    json.dumps(details),
    datetime.now()
))

conn.commit()
cursor.close()
conn.close()
```

### Using PHP
```php
<?php
$conn = new mysqli('your_db_host', 'your_db_user', 'your_db_password', 'orion');

// Simple email
$stmt = $conn->prepare("
    INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time)
    VALUES (?, ?, ?, NOW())
");
$stmt->bind_param('sss', $email, $type, $locale);
$email = 'user@example.com';
$type = 'welcome';
$locale = 'it';
$stmt->execute();

// Email with details
$stmt = $conn->prepare("
    INSERT INTO mail_queue (
        recipient_email, mail_type, locale, body_text, details_json, scheduled_time
    ) VALUES (?, ?, ?, ?, ?, NOW())
");

$details = json_encode([
    'Codice Gara' => 'R2506017',
    'Data' => '2025-06-14',
    'Arco' => 'Olimpico'
]);

$stmt->bind_param('sssss', $email, $type, $locale, $body, $details);
$email = 'user@example.com';
$type = 'invite';
$locale = 'it';
$body = "L'invito è disponibile!";
$stmt->execute();

$conn->close();
?>
```

### Using JavaScript/Node.js
```javascript
const mysql = require('mysql2/promise');

const connection = await mysql.createConnection({
    host: 'your_db_host',
    user: 'your_db_user',
    password: 'your_db_password',
    database: 'orion'
});

// Simple email
await connection.execute(
    'INSERT INTO mail_queue (recipient_email, mail_type, locale, scheduled_time) VALUES (?, ?, ?, NOW())',
    ['user@example.com', 'welcome', 'it']
);

// Email with details
const details = {
    'Codice Gara': 'R2506017',
    'Data': '2025-06-14',
    'Arco': 'Olimpico'
};

await connection.execute(
    'INSERT INTO mail_queue (recipient_email, mail_type, locale, body_text, details_json, scheduled_time) VALUES (?, ?, ?, ?, ?, NOW())',
    ['user@example.com', 'invite', 'it', "L'invito è disponibile!", JSON.stringify(details)]
);

await connection.end();
```

---

## 🔍 Useful Queries

### Check Pending Emails
```sql
SELECT id, recipient_email, mail_type, scheduled_time
FROM mail_queue
WHERE status = 'pending'
ORDER BY scheduled_time ASC;
```

### Check Recently Sent
```sql
SELECT id, recipient_email, mail_type, sent_at
FROM mail_queue
WHERE status = 'sent' AND DATE(sent_at) = CURDATE()
ORDER BY sent_at DESC;
```

### Check Errors
```sql
SELECT id, recipient_email, mail_type, error_message, updated_at
FROM mail_queue
WHERE status = 'error'
ORDER BY updated_at DESC;
```

### Queue Statistics
```sql
SELECT 
    status,
    COUNT(*) as count,
    MIN(scheduled_time) as earliest,
    MAX(scheduled_time) as latest
FROM mail_queue
GROUP BY status;
```

### Retry Failed Email
```sql
UPDATE mail_queue
SET status = 'pending', scheduled_time = NOW(), error_message = NULL
WHERE id = 123;
```

---

## ⚠️ Important Notes

### Status Management
- **DON'T** set `status` manually - mailer handles it
- **DON'T** set `sent_at` - auto-filled when sent
- **DON'T** set `error_message` - auto-filled on error

### Scheduled Time
- Use `NOW()` for immediate sending (next poll cycle)
- Use `DATE_ADD(NOW(), INTERVAL X DAY/HOUR)` for future
- Mailer only processes emails with `scheduled_time <= NOW()`

### Locale
- Default is `'it'` (Italian)
- Use `'en'` for English
- Invalid locale defaults to `'it'`

### Subject & Body
- If NULL, template defaults are used
- Custom values override templates
- Both can be customized independently

### Details JSON
- Must be valid JSON
- Keys and values both shown in email
- Use Italian keys for Italian emails
- Displays as a nice table

---

## 🚀 Quick Start Checklist

✅ **To send an email from your API:**

1. Insert row into `mail_queue` table
2. Set `recipient_email` (required)
3. Set `mail_type` (required, see list above)
4. Set `scheduled_time` (use `NOW()` for immediate)
5. Optional: add `locale`, `subject`, `body_text`, `details_json`
6. Done! Mailer picks it up within 5 seconds

**That's it!** The mailer service handles everything else automatically.
