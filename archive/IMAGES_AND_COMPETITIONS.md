# Image Updates & Competitions Page

## 🖼️ New Images Added

### Images to Upload to `/media` Directory:

1. **3d_gallery.jpg** - 3D Printing gallery section card
2. **3d_quote.jpg** - 3D Printing quote request card  
3. **3d_shop.jpg** - 3D Printing shop card
4. **el_gallery.jpg** - Electronics gallery section card
5. **el_shop.jpg** - Electronics shop card

---

## 📝 Changes Made

### 1. Updated 3D Printing Section Images

**File:** `site01/app/templates/printing/index.html`

**Changes:**
- Gallery card: `3dprinting.jpg` → `3d_gallery.jpg`
- Quote card: `3dprinting.jpg` → `3d_quote.jpg`
- Shop card: `3dprinting.jpg` → `3d_shop.jpg`

**Usage:**
```html
<!-- Gallery -->
<img src="{{ url_for('static', filename='media/3d_gallery.jpg') }}" alt="Gallery">

<!-- Quote -->
<img src="{{ url_for('static', filename='media/3d_quote.jpg') }}" alt="Quote">

<!-- Shop -->
<img src="{{ url_for('static', filename='media/3d_shop.jpg') }}" alt="Shop">
```

---

### 2. Updated Electronics Section Images

**File:** `site01/app/templates/electronics/index.html`

**Changes:**
- Gallery card: `circuit.jpg` → `el_gallery.jpg`
- Shop card: `circuit.jpg` → `el_shop.jpg`

**Usage:**
```html
<!-- Gallery -->
<img src="{{ url_for('static', filename='media/el_gallery.jpg') }}" alt="Gallery">

<!-- Shop -->
<img src="{{ url_for('static', filename='media/el_shop.jpg') }}" alt="Shop">
```

---

### 3. Created Competitions Page 🎯

**File:** `site01/app/templates/archery/competitions.html`

**Features:**
- ✅ Full competition management interface
- ✅ Filter tabs (Upcoming, Open Subscriptions, Past, My Subscriptions)
- ✅ Competition cards with all details
- ✅ Subscription modal with form
- ✅ Real-time updates
- ✅ Responsive design
- ✅ Dark mode support
- ✅ Fully localized (IT/EN)

#### Competition Card Features:
- Competition name and location
- Date range display
- Competition type and category
- Subscription deadline
- Status badges (Open/Upcoming/Ended)
- Subscribe button
- Details button
- Subscription status indicator

#### Subscription Modal Features:
- Turn selection (Morning/Afternoon/Any)
- Interest-only checkbox
- Notes field for special requests
- Form validation
- Success/error notifications

#### Filter Tabs:
1. **Upcoming** - Future competitions
2. **Open Subscriptions** - Currently accepting subscriptions
3. **Past** - Completed competitions
4. **My Subscriptions** - User's registered competitions

---

### 4. Updated Translations

**Files:** 
- `site01/translations/en.json`
- `site01/translations/it.json`

**New Translation Keys Added:**

```json
competitions: {
  // Tabs
  "past": "Past" / "Passate",
  "subscribed": "Subscribed" / "Iscritto",
  
  // Turn selection
  "choose_turn": "Choose a turn..." / "Scegli un turno...",
  "morning": "Morning" / "Mattina",
  "afternoon": "Afternoon" / "Pomeriggio",
  "any_turn": "Any Turn" / "Qualsiasi Turno",
  
  // Form
  "interest_only": "I'm just expressing interest..." / "Sto solo esprimendo interesse...",
  "notes_placeholder": "Add any notes..." / "Aggiungi note...",
  
  // UI
  "no_competitions": "No competitions found" / "Nessuna gara trovata",
  "subscribe_title": "Subscribe to Competition" / "Iscriviti alla Gara",
  "confirm_subscription": "Confirm Subscription" / "Conferma Iscrizione",
  "subscription_success": "Successfully subscribed!" / "Iscrizione effettuata con successo!",
  "subscription_error": "Failed to subscribe" / "Impossibile iscriversi",
  "select_turn_required": "Please select a turn" / "Seleziona un turno",
  "details": "Details" / "Dettagli",
  "open": "Open" / "Aperta",
  "ended": "Ended" / "Terminata",
  "competitions_subtitle": "Subscribe to club competitions..." / "Iscriviti alle gare del club..."
}
```

---

## 🚀 How to Deploy

### Step 1: Upload Images

Upload the 5 new images to the media folder:

```bash
# On your Orange Pi or server:
cd /path/to/mysite/media/

# Upload images (via SCP, SFTP, or directly)
# Expected files:
# - 3d_gallery.jpg
# - 3d_quote.jpg
# - 3d_shop.jpg
# - el_gallery.jpg
# - el_shop.jpg
```

Or if using Docker:

```bash
# Copy to container
docker cp 3d_gallery.jpg orion-project:/app/site01/app/static/media/
docker cp 3d_quote.jpg orion-project:/app/site01/app/static/media/
docker cp 3d_shop.jpg orion-project:/app/site01/app/static/media/
docker cp el_gallery.jpg orion-project:/app/site01/app/static/media/
docker cp el_shop.jpg orion-project:/app/site01/app/static/media/
```

### Step 2: Verify Route

The competitions route already exists in `site01/app/routes/archery.py`:

```python
@bp.route('/competitions')
@login_required
def competitions():
    """Competition management page - club members only"""
    if not current_user.is_club_member:
        return render_template('errors/403.html'), 403
    
    return render_template('archery/competitions.html')
```

### Step 3: Restart Application

```bash
# If using Docker
docker-compose restart

# Or systemctl
sudo systemctl restart orion-project
```

---

## 🧪 Testing

### Test Image Updates:

1. **3D Printing Section:**
   - Go to `/printing`
   - Verify 3 different images appear for Gallery, Quote, and Shop cards
   - Check they load correctly and display properly

2. **Electronics Section:**
   - Go to `/electronics`
   - Verify 2 different images appear for Gallery and Shop cards
   - Check they load correctly

### Test Competitions Page:

1. **Access Control:**
   - Try accessing `/archery/competitions` without login → Should redirect
   - Try accessing as non-club member → Should show 403 error
   - Login as club member → Should show competitions page

2. **Competition Listing:**
   - Check "Upcoming" tab shows future competitions
   - Check "Open Subscriptions" tab shows competitions with open registration
   - Check "Past" tab shows completed competitions
   - Check "My Subscriptions" tab shows user's registered competitions

3. **Subscribe to Competition:**
   - Click "Subscribe" button on a competition
   - Modal should open
   - Fill in turn selection
   - Optionally check "Interest Only"
   - Add notes
   - Click "Confirm Subscription"
   - Should show success notification
   - Card should update to show "Subscribed" status

4. **Responsive Design:**
   - Test on desktop (3-column grid)
   - Test on tablet (2-column grid)
   - Test on mobile (1-column grid)
   - Test modal on mobile

5. **Dark Mode:**
   - Toggle dark mode
   - Verify all elements are readable
   - Check modal in dark mode

6. **Localization:**
   - Switch to Italian → All text should be in Italian
   - Switch to English → All text should be in English

---

## 📊 API Endpoints Used

### GET `/archery/api/competitions`
Returns list of all competitions (filtered by status parameter if provided)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Indoor Championship 2025",
    "location": "Carrara",
    "start_date": "2025-11-15T09:00:00",
    "end_date": "2025-11-15T18:00:00",
    "competition_type": "Indoor",
    "category": "Senior",
    "subscription_open": true,
    "subscription_deadline": "2025-11-10T23:59:59"
  }
]
```

### POST `/archery/api/competitions/<id>/subscribe`
Subscribe user to a competition

**Request Body:**
```json
{
  "turn": "morning",
  "interest_only": false,
  "notes": "Optional notes here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription confirmed"
}
```

---

## 🎨 UI Components

### Competition Card Structure:

```
┌─────────────────────────────────────┐
│ Competition Name            [Badge] │
│ 📍 Location                        │
│ 📅 Date Range                      │
│                                     │
│ 🎯 Competition Type                │
│ 🏷️ Category                        │
│ ⏰ Deadline: Nov 10, 2025          │
│                                     │
│ ┌─────────────────────────────┐   │
│ │ ✓ Subscribed                │   │
│ └─────────────────────────────┘   │
│                                     │
│ [Subscribe]      [Details]         │
└─────────────────────────────────────┘
```

### Status Badges:
- 🟢 **Open** - Green badge (subscriptions open)
- 🔵 **Upcoming** - Blue badge (future competition)
- ⚫ **Ended** - Gray badge (past competition)

### Subscription Modal:

```
┌─────────────────────────────────────┐
│ Subscribe to Competition       [×] │
├─────────────────────────────────────┤
│ Indoor Championship 2025            │
│ Nov 15, 2025                        │
│                                     │
│ Select Turn: [Dropdown ▼]          │
│ ☐ Interest only (not definite)     │
│                                     │
│ Notes (optional):                   │
│ ┌─────────────────────────────┐   │
│ │                             │   │
│ └─────────────────────────────┘   │
│                                     │
│        [Cancel] [Confirm]          │
└─────────────────────────────────────┘
```

---

## 🔒 Security

- **Authentication Required:** All competition routes require login
- **Role-Based Access:** Only club members can access competitions page
- **CSRF Protection:** Forms include CSRF tokens
- **Input Validation:** All form inputs are validated server-side
- **Permission Checks:** API endpoints verify user permissions

---

## 📱 Responsive Breakpoints

| Screen Size | Grid Columns | Card Width |
|------------|--------------|------------|
| Mobile (<768px) | 1 | 100% |
| Tablet (768-1024px) | 2 | 50% |
| Desktop (>1024px) | 3 | 33.33% |

---

## 🎯 Future Enhancements

Potential features to add:

1. **Competition Details Page:**
   - Full competition information
   - Participant list
   - Results when available
   - Photo gallery

2. **Subscription Management:**
   - Edit subscription
   - Cancel subscription
   - Change turn preference
   - View confirmation email

3. **Notifications:**
   - Email reminders for deadlines
   - Push notifications for new competitions
   - Status updates

4. **Calendar Integration:**
   - Export to Google Calendar
   - iCal download
   - Month view of competitions

5. **Results Integration:**
   - Link to performance analysis
   - Automatic stats update after competition
   - Leaderboards

---

## 📄 Files Modified Summary

| File | Changes |
|------|---------|
| `printing/index.html` | Updated 3 image references |
| `electronics/index.html` | Updated 2 image references |
| `archery/competitions.html` | Created full page (NEW) |
| `translations/en.json` | Added 20+ competition keys |
| `translations/it.json` | Added 20+ competition keys |

---

## ✅ Checklist

Before deploying to production:

- [ ] Upload all 5 new images to `/media` folder
- [ ] Verify image file names match exactly (case-sensitive)
- [ ] Test all images load correctly in both sections
- [ ] Test competitions page as club member
- [ ] Test subscription flow end-to-end
- [ ] Test all filter tabs work correctly
- [ ] Test modal opens and closes properly
- [ ] Test form validation
- [ ] Test dark mode on all pages
- [ ] Test mobile responsive design
- [ ] Test both IT and EN translations
- [ ] Verify API endpoints return correct data

---

**Status:** ✅ Complete  
**Date:** October 9, 2025  
**Breaking Changes:** None  
**Database Changes:** None required
