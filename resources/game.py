from flask_restful import Resource, reqparse
from models.game import GameModel


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
        return

    def post(self):

        data = Game.parser.parse_args()

        # deconstruct data into [price] and [store_id] arguements
        game = GameModel(**data)

        try:
            game.save_to_db()
        except:
            return {'message': f'A database error occurred inserting game {game.name}'}, 500

        # 201 -> Created, 202 -> Accepted
        return game.json(), 201

    def delete(self, name):
        return

    def put(self, name):
        return


class GameList(Resource):
    def get(self):
        # list comprehension or lambda to get json for all items
        return {'games': [game.json() for game in GameModel.query.all()]}
