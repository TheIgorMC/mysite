-- Add password reset columns to users table
-- Run this directly in your SQLite database

ALTER TABLE users ADD COLUMN reset_token VARCHAR(256);
ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME;
CREATE INDEX ix_users_reset_token ON users(reset_token);

-- Verify columns were added
-- PRAGMA table_info(users);
