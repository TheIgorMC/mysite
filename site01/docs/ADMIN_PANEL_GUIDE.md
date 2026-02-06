# 🎨 Admin Panel for Athlete Management - Complete

## ✅ What Was Added

### New Admin UI Page: `/admin/manage-athletes`

A complete, user-friendly interface for admins to manage which athletes users can register for competitions.

---

## 🖥️ Features

### Left Panel: User Selection
- **Search users** by username or email (real-time filtering)
- **List all users** with admin badges
- **Click to select** a user to manage their athletes

### Left Panel: Athlete Search  
- **Search athletes** from FastAPI archery database
- **Type name or tessera** - results appear in real-time
- **Shows category** and athlete details
- **Filters out already assigned** athletes
- **One-click add** button

### Right Panel: User's Athletes
- **Shows selected user** info (username, email)
- **Athletes count** badge
- **List of assigned athletes** with:
  - Tessera number
  - Full name
  - Category
  - Birth date (if available)
- **Remove button** for each athlete (with confirmation modal)

### Safety Features
- ✅ **Confirmation modal** before removing athletes
- ✅ **Real-time updates** after add/remove
- ✅ **Prevents duplicates** - already assigned athletes don't show in search
- ✅ **Admin-only access** - requires admin privileges

---

## 🔗 New Routes Added

### Backend (main.py):
```python
GET  /admin/manage-athletes  # Render the admin page
GET  /admin/dashboard        # Admin dashboard alias
```

### API (api.py):
```python
GET  /admin/api/users                           # Get all users
GET  /admin/api/authorized-athletes?user_id=X   # Get athletes for specific user
POST /admin/api/authorized-athletes             # Add athletes to user
DELETE /admin/api/authorized-athletes/<id>      # Remove athlete
```

---

## 🚀 How to Use

### 1. Access the Page
As an admin, go to:
```
http://localhost:5000/admin
```

Click the **"Manage Athletes"** card (blue gradient) at the top.

Or directly:
```
http://localhost:5000/admin/manage-athletes
```

### 2. Select a User
- Type in the search box to filter users
- Click on a user card
- Right panel shows their info and current athletes

### 3. Add an Athlete
- Type athlete name or tessera in search (min 2 characters)
- Results appear from FastAPI database
- Click **"+ Add"** button on an athlete
- Athlete is immediately added to user's list
- Success notification appears

### 4. Remove an Athlete
- Click the **trash icon** next to an athlete
- Confirmation modal appears
- Click **"Remove"** to confirm
- Athlete is removed from user's list
- Success notification appears

---

## 📊 Data Flow

```
1. Admin searches for athlete
   ↓
2. Frontend → FastAPI GET /api/atleti?q=nome
   ↓
3. Results displayed (excluding already assigned)
   ↓
4. Admin clicks "Add"
   ↓
5. Frontend → Flask POST /admin/api/authorized-athletes
   ↓
6. Flask inserts into authorized_athletes table
   ↓
7. Success → reload user's athletes
   ↓
8. User can now subscribe this athlete to competitions
```

---

## 🎯 Integration with Competitions

Once an athlete is assigned to a user:

1. User logs in
2. Goes to **Archery → Competitions**
3. Clicks **"Subscribe"** on a competition
4. Sees dropdown with their authorized athletes:
   - `ABC123 - Mario Rossi`
   - `ABC124 - Luigi Verdi`
5. Selects athlete and turn
6. Subscription created in FastAPI with that athlete's tessera

---

## 🔧 Configuration

### Update FastAPI URL
In `manage_athletes.html`, line ~285:
```javascript
const ARCHERY_API_BASE = 'http://localhost:80/api';  // Your FastAPI URL
```

### Admin Access Required
Only users with `is_admin=True` can access this page. To make a user admin:
```sql
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
```

---

## 📱 UI Highlights

### Responsive Design
- ✅ **Desktop**: Two-column layout (search left, details right)
- ✅ **Mobile**: Stacks vertically
- ✅ **Dark mode** fully supported

### Visual Feedback
- **Selected user** highlighted with blue border
- **Assigned athletes** shown in green cards
- **Search results** appear in real-time
- **Loading spinners** during API calls
- **Success/error notifications** for all actions

### Smart UX
- **Debounced search** (300ms for users, 500ms for athletes)
- **Auto-filters** already assigned athletes from search
- **Confirmation** required before deletion
- **Clear feedback** on every action

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No athletes found" | Check FastAPI is running at configured URL |
| Can't access page | Ensure user has `is_admin=True` in database |
| Athletes not loading | Verify `/api/atleti` endpoint works in FastAPI |
| Add button not working | Check browser console for errors, verify API endpoint |
| Changes not saving | Check Flask database write permissions |

---

## 📝 Files Modified/Created

1. ✅ `app/templates/admin/manage_athletes.html` - NEW (complete UI)
2. ✅ `app/routes/main.py` - UPDATED (added `/admin/manage-athletes` route)
3. ✅ `app/routes/api.py` - UPDATED (added `/admin/api/users` endpoint)
4. ✅ `app/templates/admin.html` - UPDATED (added "Manage Athletes" card)

---

## 🎉 What You Can Do Now

✅ **Admin can search users** by username or email  
✅ **Admin can search athletes** from archery database  
✅ **Admin can assign athletes** to users with one click  
✅ **Admin can remove athletes** from users (with confirmation)  
✅ **Real-time updates** - changes reflect immediately  
✅ **Beautiful UI** - professional, responsive, dark mode  
✅ **Safe operations** - confirmations prevent mistakes  

---

## �️ Gallery Blog Editor

### Overview
Admins can transform gallery projects (3D Printing and Electronics) into full blog posts with rich HTML content.

### Access the Editor
1. Navigate to **Gallery** section
2. Click **"Edit"** on any project
3. Scroll to **"Blog Content"** section

### Features

#### 1. Dual Editor Modes
- **WYSIWYG Mode**: Rich text editor (Quill.js) with toolbar
  - Bold, italic, underline, strikethrough
  - Headers (H1, H2, H3)
  - Lists (ordered/unordered)
  - Links, images, code blocks
  - Color picker
- **HTML Raw Mode**: Direct HTML editing
  - Click **"Modalità HTML"** button to toggle
  - Paste raw HTML code
  - Full control over markup

#### 2. Live Preview
- Real-time preview of blog content
- Switch between Italian and English
- Preview updates automatically (500ms debounce)
- See exactly how the post will look

#### 3. PCB Parallax Background (Electronics Only)
- Upload PCB screenshot for parallax effect
- Recommended: 2:3 or 3:4 vertical aspect ratio (e.g., 1200x1800px)
- Effect: Background moves slowly when scrolling (inverted parallax)
- Semi-transparent glassmorphism boxes over background

#### 4. Gallery Image Management
- **Add Multiple Images**: Select multiple files at once
- **Remove Images**: Click trash icon on each image
- **Reorder**: Primary image first, then additional images
- **JSON Tracking**: Internally tracked as JSON array

#### 5. Statistics
- **View Count**: Track how many times the blog post was viewed
- **Reset Button**: Admin can reset statistics (with confirmation)

#### 6. SEO-Friendly Slugs
- Auto-generated from project title
- Editable for custom URLs
- Unique validation (prevents duplicates)
- Format: lowercase, hyphens, no special characters

### Editor Workflow

```
1. Admin clicks "Edit" on gallery project
   ↓
2. Fills in blog content (IT and EN)
   ↓
3. Chooses editor mode (WYSIWYG or HTML)
   ↓
4. Checks live preview
   ↓
5. Uploads PCB background (electronics only)
   ↓
6. Adds/removes gallery images
   ↓
7. Reviews slug (auto-generated or custom)
   ↓
8. Saves project
   ↓
9. Blog post available at /project/[slug]
```

### Button Hierarchy on Gallery Pages
After creating blog content:
- **Primary Button**: "Read Blog Post" (leads to full blog)
- **Secondary Button**: "View on GitHub/Printables" (external link)
- Both buttons appear when both slug and external_url exist

### Technical Notes
- **Database Fields**: `content_it`, `content_en`, `slug`, `pcb_background`, `updated_at`, `view_count`
- **Migration Required**: Run `migrations/add_blog_fields_to_gallery.py` once
- **Editor Library**: Quill.js 1.3.6 with Snow theme
- **Dark Mode**: Full support with custom CSS
- **File Uploads**: Main image, PCB background, multiple gallery images

### Routes
```python
GET  /admin/gallery/edit/<id>     # Edit gallery project (shows blog editor)
POST /admin/gallery/edit/<id>     # Save blog content and images
POST /admin/gallery/reset-stats/<id>  # Reset view count
GET  /project/<slug>               # Public blog post view (increments view count)
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Preview shows escaped HTML | Use "Modalità HTML" button to toggle raw mode |
| PCB background not visible | Check opacity (0.12), ensure image uploaded to correct path |
| Slug already exists | Change slug to make it unique |
| Images not uploading | Check file size limits, verify upload directory permissions |
| Dark mode editor hard to read | Refresh page, check custom CSS loaded correctly |

---

## �🚀 Next Steps (Optional Enhancements)

1. **Bulk operations** - Assign multiple athletes at once
2. **Import from CSV** - Upload athlete assignments in bulk
3. **Audit log** - Track who assigned which athlete when
4. **User notifications** - Email users when athletes are assigned
5. **Self-service requests** - Users can request athlete assignments
6. **Athlete profiles** - View full athlete history and stats
7. **Permission levels** - Different access levels (read-only, edit, etc.)

---

**The admin panel is ready to use!** Just run your Flask app and FastAPI, then visit `/admin/manage-athletes` as an admin user. 🎨
