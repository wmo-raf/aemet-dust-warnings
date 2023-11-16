from geoalchemy2 import Geometry

from dustwarning import db


class Boundary(db.Model):
    __tablename__ = "aemet_country_boundary"

    gid = db.Column(db.String(256), primary_key=True)
    country_iso = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    geom = db.Column(Geometry(geometry_type="MultiPolygon", srid=4326), nullable=False)

    def __init__(self, gid, country_iso, name, geom):
        self.gid = gid
        self.country_iso = country_iso
        self.name = name
        self.geom = geom

    def __repr__(self):
        return '<Boundary %r>' % self.name

    def serialize(self):
        """Return object data in easily serializable format"""
        boundary = {
            "gid": self.gid,
            "name": self.name,
            "country_iso": self.country_iso
        }

        return boundary


class DustWarning(db.Model):
    __tablename__ = "aemet_dust_warning"
    __table_args__ = (
        db.UniqueConstraint("gid", "init_date", "forecast_date", name='unique_dust_warming_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(db.String(256), db.ForeignKey('aemet_country_boundary.gid', ondelete="CASCADE"), nullable=False)
    init_date = db.Column(db.DateTime, nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Integer, nullable=False)

    def __init__(self, gid, init_date, forecast_date, value):
        self.gid = gid
        self.init_date = init_date
        self.forecast_date = forecast_date
        self.value = value

    def __repr__(self):
        return '<DustWarning %r>' % self.id

    def serialize(self):
        """Return object data in easily serializable format"""
        dust_warning = {
            "id": self.id,
            "gid": self.gid,
            "init_date": self.init_date,
            "forecast_date": self.forecast_date,
            "value": self.value,
        }

        return dust_warning
