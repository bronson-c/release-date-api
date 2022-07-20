import requests
import os
from flask import current_app
from db import db

# Models represent internal operations
# Resources represent external API operations


class GameModel(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    platform = db.Column(db.String(80))
    purchased = db.Column(db.Boolean)
    region = db.Column(db.String(80))
    release_date = db.Column(db.String(80))
    slug = db.Column(db.String(80))
    summary = db.Column(db.String(500))

    # IDGB specifications (Use expanders to avoid dealing with IGDB IDs):
    # search name, alternative name
    # Categories: main game 0, expansion 2, standalone_expansion 4, remake 8, remaster 9, expanded game 10, port 11
    # Platform: search game entry to see if platform is available. Search platform name, abbreviation, alternative name
    # ^ Where platform.name, platform.abbrv, platform.alt_name == "platform name ignore case"
    # Release date info: based on date category, format correctly for google calendar
    # ^ Region info based on given criteria. If specified use code, otherwise WW or NA
    # ^ Prefer human readable.
    # Use 'slug' value for endpoint URLs?? maybe
    # Status of release could be useful to archive in database*
    # add igdb summary to database, google calendar event
    # Possibly auto-update, could be a feature added later but need to be able to disable upon manually updating data.
    # Release Date is a seperate call after initial setup

    # SQL Database Categories:
    # ID (SQL, automatically assigned),
    # Slug (From IDGB based on given name, used for endpoint access)
    # Name (Provided by user, igdb will correct if required),
    # Release Date (based on region + platform. Platform, optionally region from user. Date from IGDB.),
    # Platform (Provided by user, igdb will correct if required),
    # Region (Optionally provided by user. If not provided defalut to WW or NA, whichever is available.)
    # Purchased (Boolean, provided by user/google calendar as an update)
    # Status (IDGB, save for feature expansion)
    # Summary (IGDB, save for addition to google calendar entries)

    # IDGB Query (Init):
    # fields category, name, platforms.name, platform.alternative_name, platforms.abbreviation, slug, status, summary; search name;

    # Release Date Query
    # fields category, human; where game.name = "name" & platform.name = "platform" & region = 0;

    def __init__(self, name, platform, region):

        # here do igdb reqs to fill unknowns
        self.region = region
        self.idgb_init(name, platform)
        current_app.logger.info(
            "JSON for {} after idgb_init:\n{}".format(name, self.json()))

        self.release_date = self.idgb_release_date(
            self.name, self.platform, self.region)
        current_app.logger.info(
            "JSON for {} after idgb_release_date:\n{}".format(name, self.json()))

    def idgb_init(self, name, platform):

        headers = {'content-type': 'text/plain',
                   'Client-ID': os.environ.get('TWITCH_CLIENT_ID'),
                   'Authorization': ('Bearer {}'.format(os.environ['TWITCH_ACCESS_TOKEN']))
                   }

        url = 'https://api.igdb.com/v4/games'

        # TODO match name better

        body = f'fields name, platforms.name, platforms.alternative_name, platforms.abbreviation, slug, summary; where category = (0,2,4,8, 9, 10, 11); search "{name}";'

        response = requests.post(url, data=body, headers=headers)
        current_app.logger.info(
            "IGDB init response for {} JSON: {}".format(name, response.json()))

        game_result = response.json()[0]
        self.name = game_result['name']
        self.slug = game_result['slug']
        self.summary = game_result['summary']

        for p in game_result['platforms']:
            # TODO make list and check if platform in list
            if platform.strip().casefold() == p['name'].strip().casefold() or platform.strip().casefold() == p['alternative_name'].strip().casefold() or platform.strip().casefold() == p['abbreviation'].strip().casefold():
                self.platform = p['name']
        # if self.platform is empty after this, throw error

    def region_to_id(self, region):
        cmpstr = region.strip().casefold()

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

        return region_map[cmpstr]

    def idgb_release_date(self, name, platform, region):
        # TODO Default regions, improve guessing for na/ww
        if region is None:
            region_id = '(1, 2, 8)'
        else:
            region_id = f'({self.region_to_id(region)})'

        headers = {'content-type': 'text/plain',
                   'Client-ID': os.environ.get('TWITCH_CLIENT_ID'),
                   'Authorization': ('Bearer {}'.format(os.environ['TWITCH_ACCESS_TOKEN']))
                   }

        url = 'https://api.igdb.com/v4/release_dates'

        body = f'fields category, human; where game.name = "{name}" & platform.name = "{platform}" & region = {region_id};'

        response = requests.post(url, data=body, headers=headers)
        current_app.logger.info(
            "IGDB release date response for {} JSON: {}".format(name, response.json()))

        result = response.json()[0]

        return result['human']

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'purchased': self.purchased,
            'region': self.region,
            'release_date': self.release_date,
            'slug': self.slug,
            'summary': self.summary
        }

    def save_to_db(self):
        current_app.logger.info("Before save JSON: {}".format(self.json()))
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    # @classmethod
    # def find_by_name(cls, name):
    #     # SELECT * FROM items WHERE name=name LIMIT 1
    #     return cls.query.filter_by(name=name).first()
