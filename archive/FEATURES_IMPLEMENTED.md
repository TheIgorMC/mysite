# Features Implemented - Competition System

## ✅ Feature 1: Show Region 06 Competitions WITHOUT Published Invites

**What Changed:**
- **KEPT** the regional filter for Veneto (region 06 / societa_codice starting with '06')
- **ADDED** logic to show competitions WITHOUT published invites (no turni)
- **ADDED** "Express Interest" mode for competitions without invites
- Users can now see ALL region 06 competitions, including those not yet open for registration

**Files Modified:**
- `site01/app/templates/archery/competitions.html`
  - Modified `openSubscriptionModal()` to check if turns exist
  - Added `showExpressInterestMode()` function for competitions without invites
  - Added `showNormalSubscriptionMode()` function for competitions with invites
  - Updated `submitSubscription()` to handle express interest (turno=0, special note)
  - Turn selection is hidden for express interest mode
  - Yellow info banner explains invite not yet published

**User Impact:**
- Competition list shows ALL Veneto (06) competitions
- Competitions WITHOUT invites show "Express Interest" button
- Competitions WITH invites show normal "Subscribe" button
- "Express Interest" creates a pending subscription with turno=0
- Admin can see these interest expressions in the system
- Users notified when actual invites are published (manual process)

**Technical Details:**
- Check for published invite: `GET /api/turni?codice_gara={code}` returns empty array
- Express interest stored as: `turno: 0`, `note: "Interesse espresso (invito non pubblicato). {user_notes}"`
- Modal adapts UI based on invite availability

---

## ✅ Feature 2: Delete Subscription Button

**What Changed:**
- Added DELETE endpoint: `/archery/api/iscrizioni/{id}`
- Added delete button (trash icon) next to subscribed competitions
- Confirmation dialog before deletion
- Success/error notifications
- Automatic refresh of competition list after deletion

**Files Modified:**

1. **API Client** - `site01/app/api/__init__.py`
   - Added `delete_subscription(subscription_id)` method to OrionAPIClient

2. **Flask Routes** - `site01/app/routes/archery.py`
   - Added `DELETE /api/iscrizioni/<int:subscription_id>` endpoint
   - Proxies delete request to FastAPI with Cloudflare auth

3. **Frontend** - `site01/app/templates/archery/competitions.html`
   - Changed `userSubscriptions` from Set to Map to store subscription IDs
   - Modified `loadUserSubscriptions()` to store full subscription objects
   - Updated subscription status section to include delete button
   - Added `deleteSubscription(subscription, competition)` function
   - Added confirmation dialog with translated messages
   - Wired up delete button in `renderCompetitions()`

4. **Translations** - `site01/translations/en.json` & `it.json`
   - Added `delete_subscription`: "Delete Subscription" / "Elimina Iscrizione"
   - Added `confirm_delete`: confirmation message
   - Added `delete_success`: success message
   - Added `delete_error`: error message
   - Added `express_interest_title`: "Express Interest in Competition" / "Esprimi Interesse per la Gara"
   - Added `express_interest_btn`: "Express Interest" / "Esprimi Interesse"
   - Added `no_invite_title`: "Invite Not Yet Published" / "Invito Non Ancora Pubblicato"
   - Added `no_invite_desc`: explanation text in both languages

**User Impact:**
- Users can now delete their own subscriptions
- Trash icon appears in green subscription status box
- Confirmation dialog prevents accidental deletions
- Italian translations for all messages
- Real-time UI update after deletion

---

## 🚀 Deployment Instructions

### 1. Commit Changes Locally
```bash
cd c:\Users\Mattia\Documents\GitHub\mysite
git add .
git commit -m "feat: Show all competitions + add delete subscription button"
git push origin main
```

### 2. Deploy to Server
SSH into your Orange Pi server and run:

```bash
cd /path/to/mysite
git pull origin main
docker-compose down
docker-compose build --no-cache --pull
docker-compose up -d
```

### 3. Verify Deployment
Run the check script:
```bash
bash check_deployment.sh
```

Or manually verify:
```bash
# Check container is running
docker ps | grep orion-project

# Check for new code
docker exec orion-project grep -n "deleteSubscription" /app/site01/app/templates/archery/competitions.html

# Check API endpoint exists
docker exec orion-project grep -n "delete_iscrizione" /app/site01/app/routes/archery.py
```

### 4. Test in Browser
1. **Hard refresh** your browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Navigate to Competitions page
3. **Test 1 - All Competitions Visible:**
   - Should see competitions from all regions, not just Tuscany
   - Check if you see more competitions than before
4. **Test 2 - Delete Subscription:**
   - Find a competition you're subscribed to
   - Click the trash icon in the green subscription box
   - Confirm deletion
   - Verify subscription is removed and competition card updates

---

## 📝 Technical Details

### API Flow for Delete
```
Frontend                Flask Proxy              FastAPI
   |                        |                       |
   |--- DELETE /archery/api/iscrizioni/{id} ------->|
   |                        |                       |
   |                        |-- DELETE /api/iscrizioni/{id} -->
   |                        |   (with CF auth)      |
   |                        |                       |
   |                        |<--- {"id": 182, "status": "deleted"}
   |                        |                       |
   |<--- {"id": 182, "status": "deleted"} ---------|
   |                        |                       |
```

### Subscription Object Structure
```javascript
{
  id: 182,                    // Subscription ID from database
  codice_gara: "25A001",      // Competition code
  tessera_atleta: "012345",   // Athlete ID
  categoria: "CO",            // Category
  turno: 1,                   // Turn number
  stato: "in attesa",         // Status
  note: "Notes..."            // Optional notes
}
```

---

## ⚠️ Important Notes

1. **Session State**: Users need to hard refresh after deployment to clear cached JavaScript
2. **Database**: No migration needed - uses existing API endpoints
3. **FastAPI**: The DELETE endpoint must exist in your FastAPI backend (check APIspec.md)
4. **Cloudflare Access**: Flask proxy handles authentication automatically
5. **Multiple Athletes**: If user has multiple athletes subscribed to same competition, only first subscription is shown/deleted

---

## 🔮 Future Enhancements (Optional)

1. **Soft Delete**: Add "undo" option for accidental deletions
2. **Batch Delete**: Allow deleting multiple subscriptions at once
3. **Edit Subscription**: Add edit button to change turn/category/notes
4. **Subscription History**: Show deleted subscriptions with timestamps
5. **Admin Override**: Prevent users from deleting admin-confirmed subscriptions

---

## ✅ Checklist

After deployment, verify:
- [ ] Only Region 06 (Veneto) competitions are visible
- [ ] Competitions WITH published invites show "Subscribe" button and turn selection
- [ ] Competitions WITHOUT published invites show "Express Interest" button
- [ ] Yellow info banner appears for competitions without invites
- [ ] "Express Interest" submissions work (turno=0, special note)
- [ ] Delete button (trash icon) appears on subscribed competitions
- [ ] Clicking delete shows Italian confirmation dialog
- [ ] Successful deletion shows green success message
- [ ] Competition card updates immediately after deletion
- [ ] "My Subscriptions" tab refreshes correctly
- [ ] Error handling works (network errors, invalid IDs, etc.)

---

## 📞 Support

If issues occur:
1. Check browser console for JavaScript errors (F12)
2. Check Flask logs: `docker logs orion-project`
3. Check FastAPI logs (if separate container)
4. Verify FastAPI has DELETE endpoint: `curl -X DELETE http://api/iscrizioni/123`
5. Review `APIspec.md` for expected API behavior

---

**Status**: ✅ Ready for deployment
**Date**: 2025-01-23
**Changes**: 5 files modified, 2 features added, 4 translation keys added
