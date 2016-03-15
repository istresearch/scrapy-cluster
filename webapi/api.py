import sys
sys.path.append("../kafka-monitor")

import json

from flask import request, url_for
from flask.ext.api import FlaskAPI, status, exceptions

from jsonschema import validate, ValidationError


from kafka_monitor import KafkaMonitor


kf = KafkaMonitor("localsettings.py")
kf.setup(level=None, log_file=None, json=None)

app = FlaskAPI(__name__)



@app.route('/crawl/start/', methods=['GET', 'POST'])
def crawl_start():

    schema = json.load(open('../kafka-monitor/plugins/scraper_schema.json'))
    try:
        validate(request.data, schema)
    except ValidationError as e:
        return {'request': request.data, 'error': str(e)}

    resp = kf.feed(request.data)

    return {'request': request.data, 'response': resp}


@app.route('/crawl/info/', methods=['GET', 'POST'])
def crawl_info():

    schema = json.load(open('../kafka-monitor/plugins/action_schema.json'))
    data = request.data
    data['action'] = "info"
    try:
        validate(request.data, schema)
    except ValidationError as e:
        return {'request': request.data, 'error': str(e)}

    resp = kf.feed(request.data)

    return {'request': request.data, 'response': resp}



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
