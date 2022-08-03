import json
from flask_restful import Resource, reqparse
from models.game import GameModel, GameNotFoundError, PlatformNotFoundError, InvalidRegionError, RegionNotFoundError, ReleaseDateNotFoundError


class Game(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        'name',
        type=str,
        required=True,
        help="The name of the game is required"
    )
    parser.add_argument(
        'platform',
        type=str,
        required=True,
        help="The platform of the game is required"
    )

    parser.add_argument(
        'region',
        type=str,
        required=False,
        help="Must be the name or abbreviation of an IDGB region"
    )

    def get(self, name):
        # TODO get by id and/or by 3 params (name, platform region)
        return

    def post(self):

        # TODO Get this data from a Twilio SMS message
        data = Game.parser.parse_args()

        try:
            game = GameModel(**data)
        except GameNotFoundError as e:
            return {'message': str(e)}, 400
        except PlatformNotFoundError as e:
            return {'message': str(e)}, 400
        except ReleaseDateNotFoundError as e:
            return {'message': str(e)}, 400
        except InvalidRegionError as e:
            return {'message': str(e)}, 400
        except RegionNotFoundError as e:
            return {'message': str(e)}, 400

        try:
            game.save_to_db()
        except:
            return {'message': f'A database error occurred inserting game {game.name}'}, 500

        # TODO after creation in db, create google calendar event with game info
        return game.json(), 201

    def delete(self, name):
        # TODO delete by id, and/or by 3 params (name, platform region)
        return

    def put(self, name):
        # TODO put by id, and/or by 3 params (name, platform region)
        # Updates will be received by Twilio and update google calendar events
        return


class GameList(Resource):
    def get(self):
        # list comprehension or lambda to get json for all items
        return {'games': [game.json() for game in GameModel.query.all()]}
