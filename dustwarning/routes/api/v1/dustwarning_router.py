import logging
from datetime import timedelta

from flask import jsonify
from sqlalchemy import desc

from dustwarning.models import DustWarning

from dustwarning.routes.api.v1 import endpoints


@endpoints.route('/available-forecast-dates.json', strict_slashes=False, methods=['GET'])
def get_available_dates():
    logging.info('[ROUTER]: Getting available dates')

    dates = []

    latest_init_date = DustWarning.query.order_by(desc(DustWarning.init_date)).first()

    if latest_init_date:
        latest_init_date = latest_init_date.init_date - timedelta(days=1)
        dates.append(latest_init_date)

        # add next two days
        for i in range(1, 3):
            dates.append(latest_init_date + timedelta(days=i))

    dates = [date.strftime("%Y-%m-%dT%H:%M:%S.000Z") for date in dates]

    response = {
        "timestamps": dates
    }

    return jsonify(response), 200
