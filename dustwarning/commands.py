import json
import logging
import os
from datetime import datetime

import click
from sqlalchemy import func
from sqlalchemy.sql import text

from dustwarning import db
from dustwarning.config import SETTINGS
from .mapping import boundary_config
from .models import Boundary, DustWarning
from .utils import read_state, get_next_day, get_json_warnings, update_state

BOUNDARY_DATA_DIR = SETTINGS.get("BOUNDARY_DATA_DIR")


@click.command(name="setup_schema")
def setup_schema():
    logging.info("[DBSETUP]: Setting up schema")
    schema_sql = f"""DO
                $do$
                BEGIN
                    CREATE EXTENSION IF NOT EXISTS postgis;
                    CREATE SCHEMA IF NOT EXISTS aemet;
                END
                $do$;"""

    db.session.execute(text(schema_sql))
    db.session.commit()

    logging.info("[DBSETUP]: Done Setting up schema")


@click.command(name="load_boundaries")
def load_boundaries():
    logging.info("[BOUNDARY LOADING]: Loading boundaries")

    if not os.path.exists(BOUNDARY_DATA_DIR):
        logging.info("[BOUNDARY LOADING]: Boundary data directory does not exist")
        return

    for c, config in boundary_config.items():
        iso = config.get("iso")

        geojson_file = os.path.join(BOUNDARY_DATA_DIR, f"{iso.lower()}.geojson")

        if not os.path.exists(geojson_file):
            logging.info(f"[BOUNDARY LOADING]: File {geojson_file} does not exist")
            continue

        logging.info(f"[BOUNDARY LOADING]: Loading {geojson_file}")

        id_field = config.get("id_field")
        name_field = config.get("name_field")

        with open(geojson_file, "r") as f:
            geojson = json.load(f)

            features = geojson.get("features")

            for feature in features:
                props = feature.get("properties")

                id_prop = props.get(id_field)
                name = props.get(name_field)

                if id_prop is None and name is None:
                    logging.info(f"[BOUNDARY]: Skipping ")
                    continue

                gid = f"{iso}_{id_prop}"

                geom = feature.get("geometry")
                geom_type = geom.get("type")

                # convert to multipolygon
                if geom_type == "Polygon":
                    geom = {
                        "type": "MultiPolygon",
                        "coordinates": [geom.get("coordinates")]
                    }

                boundary_data = {
                    "gid": gid,
                    "country_iso": iso,
                    "name": name,
                    "geom": func.ST_GeomFromGeoJSON(json.dumps(geom))
                }

                db_boundary = Boundary.query.get(boundary_data.get("gid"))
                exists = False

                if db_boundary:
                    exists = True

                db_boundary = Boundary(**boundary_data)

                if exists:
                    logging.info('[BOUNDARY]: UPDATE')
                    db.session.merge(db_boundary)
                else:
                    logging.info('[BOUNDARY]: ADD')
                    db.session.add(db_boundary)

                db.session.commit()


@click.command(name="load_warnings")
def load_warnings():
    state = read_state()

    day_vals = {
        "day_one_val": "0",
        "day_two_val": "1",
        "day_three_val": "2"
    }

    last_update = state.get("last_update")

    if last_update:
        next_update = get_next_day(last_update)
    else:
        next_update = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if next_update:
        next_update_str = next_update.strftime("%Y%m%d")

        for c, config in boundary_config.items():
            country_iso = config.get("iso")
            id_field = config.get("id_field")
            name_field = config.get("name_field")

            geojson_url_template = config.get("geojson_url_template")

            warnings_data = {}

            for day_val_key, day_val in day_vals.items():
                geojson_url = geojson_url_template.format(date_str=next_update_str, day_val=day_val)

                logging.info(f"[WARNINGS]: Fetching warnings for date {next_update_str} and day {day_val}")

                try:
                    geojson_warnings = get_json_warnings(geojson_url)

                    if not geojson_warnings:
                        logging.warning(f"[WARNINGS]: No warnings found for {geojson_url}")
                        return False

                    if geojson_warnings:
                        features = geojson_warnings.get("features")

                        if not features:
                            logging.warning(f"[WARNINGS]: No features found for {geojson_url}")
                            return False

                        for feature in features:
                            props = feature.get("properties")

                            id_prop = props.get(id_field)
                            name = props.get(name_field)

                            if id_prop is None and name is None:
                                logging.info(f"[WARNINGS]: Skipping ")
                                return False

                            gid = f"{country_iso}_{id_prop}"
                            value = props.get("value")

                            if not warnings_data.get(gid):
                                warnings_data[gid] = {
                                    "gid": gid,
                                    "init_date": next_update,
                                    day_val_key: value
                                }
                            else:
                                warnings_data[gid][day_val_key] = value
                except Exception as e:
                    logging.info(f"[WARNINGS]: {e}")
                    return False

            for gid, warning_data in warnings_data.items():
                db_warning = DustWarning.query.filter_by(init_date=warning_data.get("init_date"), gid=gid).first()
                exists = False

                if db_warning:
                    exists = True

                db_warning = DustWarning(**warning_data)

                if exists:
                    logging.info('[WARNING]: UPDATE')

                    for day_val_key, day_val in day_vals.items():
                        setattr(db_warning, day_val_key, warning_data.get(day_val_key))

                else:
                    logging.info('[WARNING]: ADD')
                    db.session.add(db_warning)

                db.session.commit()

        update_state(next_update.isoformat())

        logging.info(f"[WARNINGS]: Done fetching warnings for date {next_update_str}")