"""Add password reset token fields

Revision ID: add_password_reset
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add password reset fields to users table
    op.add_column('users', sa.Column('reset_token', sa.String(256), nullable=True))
    op.add_column('users', sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))
    op.create_index('ix_users_reset_token', 'users', ['reset_token'])


def downgrade():
    op.drop_index('ix_users_reset_token', 'users')
    op.drop_column('users', 'reset_token_expiry')
    op.drop_column('users', 'reset_token')
