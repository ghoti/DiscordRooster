import aiohttp
import asyncio
from pprint import pprint
import pyowm
from pyowm.exceptions.not_found_error import NotFoundError
from config.credentials import WEATHER_API


def weather(city=None):
    if not city:
        return weather('Reykjavik')
    owm = pyowm.OWM(WEATHER_API)

    try:
        conditions = owm.weather_at_place(city)
    except NotFoundError:
        return 'City Not found, try again'
    if conditions:
        return 'Current Conditions of {}: {}F/{}C at {}% Humidity and {}'.format(conditions.get_location().get_name(), conditions.get_weather().get_temperature('fahrenheit')['temp'],
                                                                 conditions.get_weather().get_temperature('celsius')['temp'], conditions.get_weather().get_humidity(),conditions.get_weather().get_detailed_status())

if __name__ == '__main__':
    print(weather('hubert nc'))
    print(weather('jacksonville,nc'))
    print(weather())
    print(weather('kjasfklewrmndzkljf'))
