# Gallery Blog System - Documentazione

**Data**: 6 Febbraio 2026  
**Ultima Modifica**: 6 Febbraio 2026
**Funzionalità**: Trasformazione progetti Gallery in Blog Post completi con effetto parallax PCB

## 📋 Panoramica

I progetti nelle categorie **3D Printing** ed **Electronics** della gallery sono stati trasformati in vere e proprie pagine blog con:

- Contenuto completo HTML/Markdown
- URL SEO-friendly con slug personalizzabili
- Effetto parallax PCB per progetti elettronici (sfondo sbroglio che si muove mentre scrolli)
- Editor WYSIWYG integrato nell'admin con modalità HTML raw
- **Live Preview** in tempo reale
- Gestione galleria immagini (aggiungi/rimuovi)
- Statistiche visualizzazioni con reset admin
- Progetti correlati automatici
- Mobile-responsive con glassmorphism

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
<div class="pcb-parallax" id="pcb-bg" style="
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: -2 !important;
    opacity: 0.12 !important;
    background-image: url(...) !important;
    background-size: 100% auto !important;
    background-position: bottom center !important;
    background-repeat: no-repeat !important;
"></div>
<div class="pcb-overlay" style="
    position: fixed !important;
    z-index: -1 !important;
    pointer-events: none !important;
"></div>
```

**JavaScript Parallax (movimento invertito):**

```javascript
document.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const parallaxSpeed = 0.3;
    // Negative value = moves UP as you scroll DOWN
    pcbBg.style.transform = `translateY(${-scrolled * parallaxSpeed}px)`;
});
```

**Configurazione Immagine PCB:**
- **Background-size**: `100% auto` - larghezza piena, altezza proporzionale (sbordo verticale)
- **Background-position**: `bottom center` - ancorata in basso
- **Movimento**: Invertito (su quando scrolli giù) per rivelare progressivamente la parte superiore
- **Aspect Ratio Consigliato**: Verticale 2:3 o 3:4 (es. 1980x3200px)
  - Formato verticale permette abbastanza spazio per il parallax
  - Evitare panoramici orizzontali
- **Opacità**: 0.12 (12%) - molto trasparente per non disturbare lettura

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
   - Main image (copertina) - sostituibile con upload
   - **Galleria Immagini Aggiuntive**:
     - Visualizzazione grid di tutte le immagini
     - Rimozione singola con conferma
     - Upload multiplo di nuove immagini
     - Preview thumbnail
   - PCB background (solo elettronica, aspect ratio 2:3 o 3:4 consigliato)
   - Upload con preview

**Gestione Galleria Immagini:**

```html
<!-- Grid immagini esistenti -->
<div id="gallery-image-{{ loop.index0 }}">
    <img src="..." />
    <button onclick="removeGalleryImage(index, filename)">
        <i class="fas fa-times"></i>
    </button>
</div>

<!-- Upload nuove -->
<input type="file" name="additional_images" multiple>
```

```javascript
function removeGalleryImage(index, filename) {
    if (confirm('Sei sicuro?')) {
        imagesToRemove.push(filename);
        document.getElementById('remove_images').value = JSON.stringify(imagesToRemove);
        // Visual feedback
        imageElement.style.opacity = '0.3';
        // Add "RIMOSSA" overlay
    }
}
```

Backend handling in `edit_project` route:
- Parse `remove_images` JSON
- Remove from images array
- Delete physical files
- Handle `additional_images` uploads
- Merge with existing images

5. **Statistiche**
   - Visualizzazioni totali
   - **Pulsante Reset Statistiche** con doppia conferma
   - Prodotti correlati
   - Date creazione/aggiornamento
   - Status attivo/inattivo

**Reset Statistiche:**

```python
@bp.route('/admin/reset_project_stats/<int:item_id>', methods=['POST'])
def reset_project_stats(item_id):
    item = GalleryItem.query.get_or_404(item_id)
    item.view_count = 0
    db.session.commit()
    return jsonify({'success': True})
```

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

**Modalità HTML Raw:**

Bottone "Modalità HTML" sopra ogni editor permette di:
- Passare da editor visuale a textarea HTML
- Incollare HTML completo direttamente
- Vedere codice sorgente
- Tornare a modalità visuale

```javascript
window.toggleRawHTML = function(lang) {
    if (rawHTMLMode[lang]) {
        // Show textarea, hide Quill
        htmlEditor.value = editor.root.innerHTML;
        htmlEditor.style.display = 'block';
        quillEditor.style.display = 'none';
    } else {
        // Show Quill, hide textarea
        editor.root.innerHTML = htmlEditor.value;
        htmlEditor.style.display = 'none';
        quillEditor.style.display = 'block';
    }
}
```

**Live Preview:**

Preview in italiano/inglese in tempo reale:
- Aggiornamento ogni 500ms mentre scrivi (debounce)
- Toggle Italiano/English
- Stili identici alla pagina blog finale
- Funziona sia in modalità visuale che HTML

```javascript
quillIT.on('text-change', function() {
    if (currentPreviewLang === 'it') {
        clearTimeout(previewUpdateTimer);
        previewUpdateTimer = setTimeout(updatePreview, 500);
    }
});
```

**Salvataggio:**

```javascript
form.addEventListener('submit', function() {
    // Get from appropriate source
    var contentEN = rawHTMLMode.en 
        ? document.getElementById('html-editor-en').value 
        : quillEN.root.innerHTML;
    var contentIT = rawHTMLMode.it 
        ? document.getElementById('html-editor-it').value 
        : quillIT.root.innerHTML;
        
    document.getElementById('content_en').value = contentEN;
    document.getElementById('content_it').value = contentIT;
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

### PCB Background (Fixed, con stili inline forzati)

```css
.pcb-parallax {
    position: fixed !important;
    opacity: 0.12 !important;  /* Leggera trasparenza */
    background-size: 100% auto !important;  /* Fit orizzontale, sbordo verticale */
    background-position: bottom center !important;  /* Ancorato in basso */
    will-change: transform !important;
    z-index: -2 !important;
}

.pcb-overlay {
    /* Rimosso gradiente - glassmorphism sui box gestisce leggibilità */
    position: fixed !important;
    z-index: -1 !important;
    pointer-events: none !important;
}
```

### Glassmorphism (Box Semi-Trasparenti)

```css
/* Header */
header {
    background: rgba(255, 255, 255, 0.9);  /* 90% opacità */
    backdrop-filter: blur(12px);
    @apply bg-white/90 dark:bg-gray-900/90 backdrop-blur-md;
}

/* Description Lead */
.description-lead {
    background: rgba(255, 255, 255, 0.8);  /* 80% opacità */
    backdrop-filter: blur(8px);
    @apply bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm;
}

/* Blog Content */
.blog-content {
    background: rgba(255, 255, 255, 0.9);  /* 90% opacità */
    backdrop-filter: blur(12px);
    @apply bg-white/90 dark:bg-gray-800/90 backdrop-blur-md;
}
```

L'effetto glassmorphism permette di vedere il PCB attraverso i box con blur, mantenendo leggibilità.

### Blog Content Typography

```css
.blog-content {
    font-size: 1.125rem;  /* 18px base, 14px mobile */
    line-height: 1.8;
}
.blog-content h1 { @apply text-2rem font-bold mt-8 mb-4; }
.blog-content h2 { @apply text-3xl font-bold mt-8 mb-4; }
.blog-content h3 { @apply text-2xl font-bold mt-6 mb-3; }
.blog-content p { @apply mb-4 text-gray-700 dark:text-gray-300; }
.blog-content code { @apply bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-sm; }
.blog-content pre { @apply bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4; }
.blog-content img { @apply rounded-lg shadow-lg my-6 w-full; }
.blog-content blockquote { 
    @apply border-l-4 border-primary pl-4 ml-0 mb-4 italic; 
}
```

### Mobile Responsiveness

Responsive utility classes per mobile:
```html
<!-- Titolo scalabile -->
<h1 class="text-3xl md:text-4xl lg:text-5xl font-bold">

<!-- Padding ridotto su mobile -->
<div class="p-4 md:p-8 rounded-xl md:rounded-2xl">

<!-- Layout verticale su mobile -->
<div class="flex flex-col md:flex-row items-center gap-4">

<!-- Testo dimensionato -->
<p class="text-sm md:text-base">

<!-- Breakpoints Tailwind -->
- mobile: <640px (default)
- md: ≥768px
- lg: ≥1024px
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
✅ Effetto parallax PCB per elettronica (invertito, fit orizzontale)  
✅ Editor WYSIWYG admin (Quill.js)  
✅ **Modalità HTML raw** per incollare codice direttamente  
✅ **Live Preview** in tempo reale (IT/EN)  
✅ **Gestione galleria immagini** (aggiungi/rimuovi multiple)  
✅ **Reset statistiche** con conferma admin  
✅ Statistiche visualizzazioni  
✅ Progetti correlati automatici  
✅ Galleria immagini con modal  
✅ Responsive design (mobile-first)  
✅ **Glassmorphism** (box semi-trasparenti con blur)  
✅ Dark mode support  
✅ Migrazione automatica slug  
✅ Link a progetti esterni (GitHub/Printables) separati da link blog  

---

**Enjoy your new advanced blog system! 🚀**
