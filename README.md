# Release Date API

## Getting Started
To use the API you will need a [Twitch](https://dev.twitch.tv/) client ID and secret set as environment variables.

```
export TWITCH_CLIENT_ID=[your ID here]
export TWITCH_CLIENT_SECRET=[your secret here]
```

Once the variables of set, run the app with:
```
python app.py
``` 
and use your program of choice to send requests to the API.

## Example Usage

Sending a POST request to the /game endpoint with the body:
```
{
    "name": "The pathless",
    "platform": "ps5"
}
```

Will add a database entry with release date info based on a default region:

```
{
    "id": 1,
    "name": "The Pathless",
    "platform": "PlayStation 5",
    "purchased": null,
    "region": "Worldwide",
    "release_date": "Nov 12, 2020",
    "summary": "The Pathless is a mythic adventure where you play as the Hunter, a skilled archer who explores a mysterious cursed island with an eagle companion. Your goal is to lift an unnatural shroud of darkness that plagues the world. As you bound acrobatically through dense forests, you will hunt prey, discover ancient ruins, and form a deep bond with your eagle. But beware: dangerous spirits also lurk in the woods. If you aren't careful, you may become the hunted yourself."
}
```

Additionally region can be specified for release dates within other regions:
```
{
    "name": "13 sentinels aegis rim",
    "platform": "ps4",
    "region": "jp"
}
```
