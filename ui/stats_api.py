from flask import Flask
from flask_restful import Resource, Api
import json

app = Flask(__name__)
api = Api(app)


class Stats(Resource):
    def get(self):
        with open("stats/stats.json", 'rb') as stats_cache:
            stats = json.load(stats_cache)
        return stats

api.add_resource(Stats, '/getStats')

if __name__ == '__main__':
    app.run(debug=True)
