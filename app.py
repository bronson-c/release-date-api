import os
import requests
from flask import Flask
from flask_restful import Api
from resources.game import Game, GameList

from db import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev')
api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()

# TODO add logging


@app.before_first_request
def twitch_login():
    # TODO ensure that token does not expire.
    # Check for validity before each call to igdb
    # If token is invalid call token login again
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': os.environ.get('TWITCH_CLIENT_ID'),
        'client_secret': os.environ.get('TWITCH_CLIENT_SECRET'),
        'grant_type': 'client_credentials'
    }

    response = requests.post(url, params=params)
    os.environ['TWITCH_ACCESS_TOKEN'] = response.json()['access_token']

    app.logger.info("Twitch login response JSON: {}".format(response.json()))
    app.logger.info("Twitch access token: {}".format(
        os.environ['TWITCH_ACCESS_TOKEN']))


api.add_resource(Game, '/game')
api.add_resource(GameList, '/games')


if __name__ == '__main__':
    db.init_app(app)
    app.run(port=5000, debug=True)
