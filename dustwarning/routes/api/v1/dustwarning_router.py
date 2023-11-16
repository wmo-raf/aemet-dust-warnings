import logging

from flask import jsonify

from dustwarning.routes.api.v1 import endpoints


@endpoints.route('/dates', strict_slashes=False, methods=['GET'])
def get_available_dates():
    logging.info('[ROUTER]: Getting available dates')

    response = []

    return jsonify(response), 200
