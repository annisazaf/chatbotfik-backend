"""Add admin role + kurikulum tables

Revision ID: a3f9b1c2d4e5
Revises: 64d512e18d64
Create Date: 2026-04-15 10:00:00.000000

Perubahan:
1. Tambah kolom 'role' di tabel users (default: 'mahasiswa')
2. Buat tabel kurikulum_prodi  — master program studi & aturan akademik
3. Buat tabel mata_kuliah_kurikulum — daftar MK per prodi
"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f9b1c2d4e5'
down_revision = '64d512e18d64'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Tambah kolom role ke tabel users ──
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('role', sa.String(10), nullable=False, server_default='mahasiswa')
        )

    # ── 2. Buat tabel kurikulum_prodi ──
    op.create_table(
        'kurikulum_prodi',
        sa.Column('id',                sa.Integer(),     primary_key=True),
        sa.Column('nama_prodi',        sa.String(100),   nullable=False, unique=True),
        sa.Column('total_semester',    sa.Integer(),     nullable=False, server_default='8'),
        sa.Column('sks_lulus',         sa.Integer(),     nullable=False, server_default='144'),
        sa.Column('syarat_sidang_sks', sa.Integer(),     nullable=False, server_default='138'),
        sa.Column('is_active',         sa.Boolean(),     nullable=False, server_default='true'),
        sa.Column('peminatan_config',  sa.JSON(),        nullable=True),
        sa.Column('created_at',        sa.DateTime(),    nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at',        sa.DateTime(),    nullable=True,  onupdate=sa.func.now()),
    )

    # ── 3. Buat tabel mata_kuliah_kurikulum ──
    op.create_table(
        'mata_kuliah_kurikulum',
        sa.Column('id',         sa.Integer(),    primary_key=True),
        sa.Column('prodi_id',   sa.Integer(),    sa.ForeignKey('kurikulum_prodi.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kode',       sa.String(20),   nullable=True),
        sa.Column('nama',       sa.String(200),  nullable=False),
        sa.Column('sks',        sa.Integer(),    nullable=False),
        sa.Column('semester',   sa.Integer(),    nullable=False),
        sa.Column('keterangan', sa.String(100),  nullable=True),
        sa.Column('prasyarat',  sa.Text(),       nullable=True),
        sa.Column('urutan',     sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(),   nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(),   nullable=True,  onupdate=sa.func.now()),
    )

    # Index untuk query yang sering dipakai
    op.create_index('ix_mk_kurikulum_prodi_id', 'mata_kuliah_kurikulum', ['prodi_id'])
    op.create_index('ix_mk_kurikulum_semester',  'mata_kuliah_kurikulum', ['prodi_id', 'semester'])


def downgrade():
    op.drop_index('ix_mk_kurikulum_semester',  table_name='mata_kuliah_kurikulum')
    op.drop_index('ix_mk_kurikulum_prodi_id',  table_name='mata_kuliah_kurikulum')
    op.drop_table('mata_kuliah_kurikulum')
    op.drop_table('kurikulum_prodi')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('role')
