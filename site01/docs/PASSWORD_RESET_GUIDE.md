# Password Reset System - User Guide

## Overview
The password reset system allows users to recover their accounts and admins to help users who forgot their passwords.

## For Users

### Forgot Your Password?
1. Go to the login page
2. Click "Password Dimenticata?" (Forgot Password?)
3. Enter your email address
4. Check your email for the reset link
5. Click the link and enter your new password
6. The link expires after 24 hours

### Change Password (Logged In)
1. Go to Settings
2. Click "Change Password"
3. Enter current password
4. Enter new password twice
5. Submit

## For Administrators

### Access User Management
Navigate to: `/admin/users`

### Two Ways to Reset a User's Password

#### 1. Send Reset Email (Recommended)
- Click the **envelope icon** (<i class="fas fa-envelope"></i>) next to the user
- An email with a reset link will be sent to the user
- The user can reset their own password
- Link expires in 24 hours

#### 2. Set Password Directly
- Click the **key icon** (<i class="fas fa-key"></i>) next to the user
- Enter a new password (min. 6 characters)
- The password is set immediately
- **You should communicate the new password to the user securely**

### Use Cases

**User Lost Email Access:**
- Use "Set Password Directly"
- Give them the new password via phone/in-person
- Ask them to change it immediately after login

**User Forgot Password (Has Email):**
- Use "Send Reset Email"
- User handles the rest themselves

**Account Locked/Suspicious:**
- Use "Set Password Directly" to reset
- Then use "Send Reset Email" so user can set their own

## Database Schema

### New Fields in `users` Table
```sql
reset_token VARCHAR(256) -- Secure random token
reset_token_expiry DATETIME -- When token expires (24h from creation)
```

### Indexes
- `reset_token` is indexed for fast lookup

## Security Features

1. **Token Expiration**: Reset links expire after 24 hours
2. **Secure Tokens**: Uses `secrets.token_urlsafe(32)` for cryptographic security
3. **No Password Storage**: Tokens are separate from passwords
4. **One-Time Use**: Token is cleared after successful reset
5. **Email Validation**: Doesn't reveal if email exists (returns same message)

## Email Integration

The system uses the OrionAPIClient to send emails. If email service is unavailable:
- In development: The reset link is displayed in a flash message
- In production: Should fail gracefully and log the error

## Testing

### Test Reset Flow (Development)
1. Go to `/auth/forgot-password`
2. Enter test email
3. Copy the reset link from the flash message
4. Visit the link
5. Set new password

### Test Admin Functions
1. Login as admin
2. Go to `/admin/users`
3. Test both reset methods with a test account

## Migration

Run the migration to add the required database fields:
```bash
python migrations/add_password_reset_tokens.py
```

Or apply manually:
```sql
ALTER TABLE users ADD COLUMN reset_token VARCHAR(256);
ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME;
CREATE INDEX ix_users_reset_token ON users(reset_token);
```

## Routes Added

- `GET/POST /auth/forgot-password` - Request password reset
- `GET/POST /auth/reset-password/<token>` - Reset with token
- `GET /admin/users` - User management page (admin only)
- `POST /admin/users/<id>/force-reset-password` - Send reset email (admin)
- `POST /admin/users/<id>/set-password` - Set password directly (admin)

## Translations

All user-facing strings are in `translations/it.json` under the `auth` section.

## Future Enhancements

- [ ] Add password strength meter
- [ ] Require stronger passwords (uppercase, numbers, symbols)
- [ ] Add rate limiting to prevent brute force
- [ ] Log all password reset attempts
- [ ] Send notification email when password is changed
- [ ] Add 2FA support
