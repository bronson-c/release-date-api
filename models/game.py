import requests
import os
from flask import current_app
from db import db
from fuzzywuzzy import fuzz

REGION_PRIORITY = ['Worldwide', 'North America', 'Europe', 'Asia',
                   'Japan', 'Australia', 'New Zealand', 'Korea', 'Brazil', 'China']


class GameNotFoundError(ValueError):
    """Raised when the IDGB search cannot find any results."""
    pass


class PlatformNotFoundError(ValueError):
    """Raised when the IDGB search cannot a find game with the platform given"""
    pass


class ReleaseDateNotFoundError(ValueError):
    """Raised in the rare case a searched game has no release date info on IGDB"""
    pass


class RegionNotFoundError(ValueError):
    """Raised when the region provided is not found with the game and platform provided"""
    pass


class InvalidRegionError(ValueError):
    """Raised when the region provided cannot be mapped to an idgb region"""
    pass


class GameModel(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    platform = db.Column(db.String(80))
    purchased = db.Column(db.Boolean)
    region = db.Column(db.String(80))
    # TODO May need to change to date format rather than string for Google Calendar API
    release_date = db.Column(db.String(80))
    summary = db.Column(db.String(500))

    def __init__(self, name, platform, region):

        # Perform igdb requests to fill unknowns
        self.idgb_init(name, platform)
        current_app.logger.info("JSON for {} after idgb_init:\n{}".format(name, self.json()))

        self.idgb_release_date(
            self.name, self.platform, region)
        current_app.logger.info("JSON for {} after idgb_release_date:\n{}".format(name, self.json()))

    def idgb_init(self, name, platform):

        # Send IGDB request for required data
        headers = {'content-type': 'text/plain',
                   'Client-ID': os.environ.get('TWITCH_CLIENT_ID'),
                   'Authorization': ('Bearer {}'.format(os.environ['TWITCH_ACCESS_TOKEN']))
                   }

        url = 'https://api.igdb.com/v4/games'

        body = f'fields name, alternative_names.name, platforms.name, platforms.alternative_name, platforms.abbreviation, summary; where category = (0, 2, 4, 8, 9, 10, 11); search "{name}";'

        response = requests.post(url, data=body, headers=headers)
        current_app.logger.info(
            "IGDB init response for {} JSON: {}".format(name, response.json()))

        if not response.json():
            raise GameNotFoundError(f"The search term \"{name}\" found no results on IDGB.")

        # From IDGB results, match games that closely match user search query
        result_tuples = []
        for result in response.json():

            name_match_ratios = []

            r = fuzz.ratio(name.casefold(), result['name'].casefold())
            name_match_ratios.append(r)

            if 'alternative_names' in result:
                for alt_name in result['alternative_names']:
                    r = fuzz.ratio(name.casefold(), alt_name['name'].casefold())
                    name_match_ratios.append(r)

            current_app.logger.info("List of name match ratios for {}. {}".format(result['name'], name_match_ratios))

            # Check that game result at least matches majority of the name to be considered
            if max(name_match_ratios) > 70:
                result_tuples.append((result, max(name_match_ratios)))

        if not result_tuples:
            raise GameNotFoundError(
                f"The search term \"{name}\" found no closely matching results on IDGB. Try using a more accurate game title.")

        result_tuples.sort(key=lambda tup: tup[1], reverse=True)

        # Check closely matching results to ensure that the desired platform is available
        for tuple in result_tuples:
            game_result = tuple[0]

            platform_names = {}
            for p in game_result['platforms']:
                platform_names[p['name'].casefold()] = p['name']
                if 'alternative_name' in p:
                    platform_names[p['alternative_name'].casefold()] = p['name']
                if 'abbreviation' in p:
                    platform_names[p['abbreviation'].casefold()] = p['name']

            current_app.logger.info("Platform Names for {}: {}".format(game_result['name'], platform_names))

            if platform.casefold() in platform_names:
                self.platform = platform_names[platform.casefold()]

            if self.platform != None:
                self.name = game_result['name']
                if 'summary' in game_result:
                    self.summary = game_result['summary']
                break

        if self.platform == None:
            raise PlatformNotFoundError(
                f"The search term \"{name}\" found no results on IDGB with the platform \"{platform}\".")

    def idgb_release_date(self, name, platform, region):

        # Send IGDB request for required release date data
        headers = {'content-type': 'text/plain',
                   'Client-ID': os.environ.get('TWITCH_CLIENT_ID'),
                   'Authorization': ('Bearer {}'.format(os.environ['TWITCH_ACCESS_TOKEN']))
                   }

        url = 'https://api.igdb.com/v4/release_dates'

        # TODO Release Date 'category' field has possible use with google calendar integration
        body = f'fields category, human, region; where game.name = "{name}" & platform.name = "{platform}";'

        response = requests.post(url, data=body, headers=headers)
        current_app.logger.info(
            "IGDB release date response for {} JSON: {}".format(name, response.json()))

        if not response.json():
            raise ReleaseDateNotFoundError(
                f"The game \"{name}\" with platform \"{platform}\" has no release date information on IDGB.")

        # Dictionary mapping release date info to region string
        release_dates = {}
        for date in response.json():
            region_string = GameModel.id_to_region(date['region'])
            release_dates[region_string] = date

        # If user specified region, use only that region
        if region != None:
            region_id = GameModel.region_to_id(region)
            self.region = GameModel.id_to_region(region_id)
            if self.region in release_dates:
                self.release_date = release_dates[self.region]['human']
            else:
                raise RegionNotFoundError(
                    f"The game \"{name}\" with platform \"{platform}\" found no release dates with region {self.region}")
        else:
            # Sort regional release dates by priority, pick the highest priority
            sorted_release_dates = {region: release_dates[region]
                                    for region in REGION_PRIORITY if region in release_dates}

            release_date_result = list(sorted_release_dates.values())[0]
            self.region = GameModel.id_to_region(release_date_result['region'])
            self.release_date = release_date_result['human']

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'purchased': self.purchased,
            'region': self.region,
            'release_date': self.release_date,
            'summary': self.summary
        }

    def save_to_db(self):
        current_app.logger.info("Before save JSON: {}".format(self.json()))
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def region_to_id(region):
        cmpstr = region.casefold()

        region_map = {}
        region_map.update(dict.fromkeys(['eu', 'eur', 'europe'], 1))
        region_map.update(dict.fromkeys(['na', 'usa', 'north america'], 2))
        region_map.update(dict.fromkeys(['aus', 'australia', 'oceania'], 3))
        region_map.update(dict.fromkeys(['nz', 'new zealand'], 4))
        region_map.update(dict.fromkeys(['jp', 'jpn', 'japan'], 5))
        region_map.update(dict.fromkeys(['cn', 'roc', 'china'], 6))
        region_map.update(dict.fromkeys(['as', 'hk', 'asia', 'hong kong'], 7))
        region_map.update(dict.fromkeys(['ww', 'worldwide', 'global'], 8))
        region_map.update(dict.fromkeys(['kr', 'korea', 'south korea'], 9))
        region_map.update(dict.fromkeys(['br', 'brz', 'brazil'], 10))

        if cmpstr in region_map:
            return region_map[cmpstr]
        else:
            raise InvalidRegionError(f"The term \"{cmpstr}\" is not a vaild IDGB region.")

    @staticmethod
    def id_to_region(region_id):

        id_map = {1: 'Europe',
                  2: 'North America',
                  3: 'Australia',
                  4: 'New Zealand',
                  5: 'Japan',
                  6: 'China',
                  7: 'Asia',
                  8: 'Worldwide',
                  9: 'Korea',
                  10: 'Brazil'}

        return id_map[region_id]
