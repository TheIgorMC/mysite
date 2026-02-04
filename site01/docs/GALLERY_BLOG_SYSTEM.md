# Gallery Blog System - Documentazione

**Data**: 4 Febbraio 2026  
**Funzionalità**: Trasformazione progetti Gallery in Blog Post completi con effetto parallax PCB

## 📋 Panoramica

I progetti nelle categorie **3D Printing** ed **Electronics** della gallery sono stati trasformati in vere e proprie pagine blog con:

- Contenuto completo HTML/Markdown
- URL SEO-friendly con slug personalizzabili
- Effetto parallax PCB per progetti elettronici (sfondo sbroglio che si muove mentre scrolli)
- Editor WYSIWYG integrato nell'admin
- Statistiche visualizzazioni
- Progetti correlati automatici

## 🗄️ Modifiche Database

### Nuovi Campi in `gallery_items`

```sql
ALTER TABLE gallery_items ADD COLUMN content_it TEXT;
ALTER TABLE gallery_items ADD COLUMN content_en TEXT;
ALTER TABLE gallery_items ADD COLUMN slug VARCHAR(256) UNIQUE;
ALTER TABLE gallery_items ADD COLUMN pcb_background VARCHAR(256);
ALTER TABLE gallery_items ADD COLUMN updated_at DATETIME;
ALTER TABLE gallery_items ADD COLUMN view_count INTEGER DEFAULT 0;
CREATE UNIQUE INDEX ix_gallery_items_slug ON gallery_items(slug);
```

**Campi:**

- `content_it` / `content_en`: Contenuto completo articolo blog (HTML)
- `slug`: URL-friendly identifier (es: `arduino-weather-station`)
- `pcb_background`: Nome file immagine PCB per parallax (solo elettronica)
- `updated_at`: Data ultimo aggiornamento
- `view_count`: Contatore visualizzazioni

### Migrazione

Eseguire nel container Docker:

```bash
python /app/site01/migrations/add_blog_fields_to_gallery.py
```

Lo script:
- Aggiunge tutte le colonne necessarie
- Crea l'indice su slug
- Genera automaticamente slug per progetti esistenti
- Gestisce duplicati con contatore incrementale

## 🎨 Frontend

### Nuove Pagine

1. **`/project/<slug>`** - Singolo progetto (blog post)
   - Template: `templates/project_detail.html`
   - Effetto parallax PCB per elettronica
   - Galleria immagini con modal
   - Prodotti correlati
   - Progetti correlati (stessa categoria)
   - Link esterno GitHub/Printables
   
2. **`/projects/<category>`** - Lista progetti per categoria
   - Template: `templates/projects_list.html`
   - Grid responsive con cards
   - Metadata (views, data, tags)
   - Preview descrizione

### Effetto Parallax PCB

**Solo per categoria `electronics` con `pcb_background` impostato:**

```html
<div class="pcb-parallax" style="background-image: url(...)"></div>
<div class="pcb-overlay"></div>
```

JavaScript applica `translateY()` basato su scroll:

```javascript
document.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const parallaxSpeed = 0.3;
    pcbBg.style.transform = `translateY(${scrolled * parallaxSpeed}px)`;
});
```

**File PCB:** Upload in `static/uploads/pcb/`

## 🛠️ Admin Panel

### Editor Progetti Avanzato

**URL:** `/admin/edit_project/<item_id>`  
**Template:** `templates/admin/edit_project.html`

**Sezioni:**

1. **Informazioni Base**
   - Titoli IT/EN
   - Categoria (3D Printing / Electronics)
   - Slug (auto-generato o manuale)
   - Tags (separati da virgole)
   - Link esterno

2. **Descrizioni Brevi**
   - Testo per cards gallery (IT/EN)
   - Max 2-3 righe

3. **Contenuto Completo**
   - Editor WYSIWYG (Quill.js)
   - HTML completo articolo
   - IT/EN separati

4. **Immagini**
   - Main image (copertina)
   - PCB background (solo elettronica)
   - Upload con preview

5. **Statistiche**
   - Visualizzazioni totali
   - Prodotti correlati
   - Date creazione/aggiornamento
   - Status attivo/inattivo

**Accesso dall'admin gallery:**

Pulsante blu **"Edit Blog"** su ogni progetto.

### Quill.js Editor

**Features:**
- Headers (H1, H2, H3)
- Bold, Italic, Underline, Strike
- Liste ordinate/non ordinate
- Blockquote, Code block
- Colori testo/sfondo
- Link e immagini
- Clean formatting

**Salvataggio:**

```javascript
form.addEventListener('submit', function() {
    document.getElementById('content_en').value = quillEN.root.innerHTML;
    document.getElementById('content_it').value = quillIT.root.innerHTML;
});
```

## 🔗 Routes

### Visualizzazione Pubblica

```python
@bp.route('/project/<slug>')
def project_detail(slug):
    # Increment view count
    # Get related projects
    # Render template
```

```python
@bp.route('/projects/<category>')
def projects_by_category(category):
    # category: '3dprinting' o 'electronics'
    # Order by created_at DESC
```

### Admin

```python
@bp.route('/admin/edit_project/<int:item_id>', methods=['GET', 'POST'])
def edit_project(item_id):
    # Update all fields
    # Handle image uploads
    # Generate slug
    # Save to database
```

## 📂 Struttura File

```
uploads/
├── gallery/          # Main images progetti
│   └── abc123.jpg
└── pcb/              # Screenshot PCB per parallax
    └── pcb_def456.png

templates/
├── project_detail.html      # Singolo progetto
├── projects_list.html       # Lista categoria
└── admin/
    └── edit_project.html    # Editor admin

migrations/
└── add_blog_fields_to_gallery.py
```

## 🎯 Utilizzo

### 1. Creare Nuovo Progetto Blog

1. Admin → Gallery → "Add Gallery Item" (form base)
2. Click "Edit Blog" sul progetto creato
3. Compila contenuto completo con editor
4. (Se elettronica) Carica screenshot PCB
5. Salva

### 2. Modificare Progetto Esistente

1. Admin → Gallery
2. Click "Edit Blog" su progetto
3. Modifica campi desiderati
4. Salva

### 3. Pubblicare/Nascondere

Usa il toggle "Active/Inactive" nella gallery admin.

### 4. Generare Slug Personalizzato

Campo "URL Slug" nell'editor. Formato: `solo-lettere-minuscole-numeri-trattini`

Se vuoto, generato automaticamente dal titolo inglese.

## 🎨 Styling

### PCB Background

```css
.pcb-parallax {
    position: fixed;
    opacity: 0.08;  /* Molto trasparente */
    background-size: cover;
    will-change: transform;
}

.pcb-overlay {
    /* Gradient per migliorare leggibilità */
    background: linear-gradient(...);
}
```

### Blog Content

```css
.blog-content h2 { font-size: 3xl; }
.blog-content h3 { font-size: 2xl; }
.blog-content p { margin-bottom: 1rem; }
.blog-content code { background: gray-100; }
.blog-content pre { background: gray-100; padding: 1rem; }
.blog-content img { rounded-lg; shadow-lg; }
```

## 🔍 SEO

### URL Structure

```
/project/arduino-weather-station
/project/3d-printed-phone-holder
/projects/electronics
/projects/3dprinting
```

### Meta Tags (da aggiungere)

Nel template `project_detail.html` puoi estendere il block `head` con:

```html
{% block head %}
{{ super() }}
<meta name="description" content="{{ item.description_it }}">
<meta property="og:title" content="{{ item.title_it }}">
<meta property="og:image" content="{{ url_for('static', filename='uploads/gallery/' + item.main_image, _external=True) }}">
{% endblock %}
```

## 📊 Statistiche

### View Counter

Incrementato automaticamente ad ogni visita:

```python
item.view_count = (item.view_count or 0) + 1
db.session.commit()
```

Visualizzato in:
- Pagina progetto
- Lista progetti
- Admin stats

### Progetti Correlati

Query automatica per stessa categoria:

```python
related = GalleryItem.query.filter(
    GalleryItem.category == item.category,
    GalleryItem.id != item.id,
    GalleryItem.is_active == True
).order_by(GalleryItem.view_count.desc()).limit(3).all()
```

## 🚀 Prossimi Step

1. **Migrazione Database**: Esegui il migration script
2. **Upload PCB Screenshots**: Per progetti elettronici esistenti
3. **Scrivi Contenuti**: Popola i campi `content_it` e `content_en`
4. **Test Effetto Parallax**: Verifica su progetti electronics
5. **SEO Meta Tags**: Aggiungi OpenGraph e Twitter Cards

## 🐛 Troubleshooting

### Slug duplicato

Lo script genera automaticamente con contatore se duplicato.  
Manualmente: modifica campo slug nell'editor.

### Parallax non funziona

Verifica:
1. Categoria = "electronics"
2. Campo `pcb_background` ha valore
3. File esiste in `static/uploads/pcb/`
4. JavaScript non ha errori console

### Editor non salva

Controlla console browser. Quill.js deve essere caricato correttamente.

### Immagini non appaiono

Percorsi upload:
- Main: `static/uploads/gallery/`
- PCB: `static/uploads/pcb/`

Verifica permessi cartelle.

## 📝 Note Tecniche

- **Quill.js**: Editor salvato come HTML grezzo
- **Parallax**: Solo `position: fixed`, non affetta layout
- **Slug**: Validato con regex `[a-z0-9-]+`
- **View Count**: No autenticazione richiesta (può essere inflazionato)
- **Related**: Max 3 progetti, ordinati per popolarità

## 🎉 Features Aggiunte

✅ Blog post completi con HTML  
✅ URL SEO-friendly  
✅ Effetto parallax PCB per elettronica  
✅ Editor WYSIWYG admin  
✅ Statistiche visualizzazioni  
✅ Progetti correlati automatici  
✅ Galleria immagini con modal  
✅ Responsive design  
✅ Dark mode support  
✅ Migrazione automatica slug  

---

**Enjoy your new blog system! 🚀**
