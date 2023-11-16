"""Initial

Revision ID: 1bb385bb6278
Revises: 
Create Date: 2023-11-16 17:03:16.062648

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision = '1bb385bb6278'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_geospatial_table('aemet_country_boundary',
    sa.Column('gid', sa.String(length=256), nullable=False),
    sa.Column('country_iso', sa.String(length=3), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('geom', Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
    sa.PrimaryKeyConstraint('gid')
    )
    with op.batch_alter_table('aemet_country_boundary', schema=None) as batch_op:
        batch_op.create_geospatial_index('idx_aemet_country_boundary_geom', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})

    op.create_table('aemet_dust_warning',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('gid', sa.String(length=256), nullable=False),
    sa.Column('init_date', sa.DateTime(), nullable=False),
    sa.Column('forecast_date', sa.DateTime(), nullable=False),
    sa.Column('value', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['gid'], ['aemet_country_boundary.gid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('gid', 'init_date', 'forecast_date', name='unique_dust_warming_date')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('aemet_dust_warning')
    with op.batch_alter_table('aemet_country_boundary', schema=None) as batch_op:
        batch_op.drop_geospatial_index('idx_aemet_country_boundary_geom', postgresql_using='gist', column_name='geom')

    op.drop_geospatial_table('aemet_country_boundary')
    # ### end Alembic commands ###