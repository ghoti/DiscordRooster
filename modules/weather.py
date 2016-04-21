import aiohttp
import asyncio
from pprint import pprint
import pyowm
from config.credentials import WEATHER_API


def weather(city=None):
    if not city:
        return weather('Reykjavik')
    owm = pyowm.OWM(WEATHER_API)

    conditions = owm.weather_at_place(city)
    if conditions:
        return 'Current Conditions of {}: {}F/{}C and {}'.format(conditions.get_location().get_name(), conditions.get_weather().get_temperature('fahrenheit')['temp'],
                                                                 conditions.get_weather().get_temperature('celsius')['temp'] ,conditions.get_weather().get_detailed_status())
    else:
        return 'City not found, try again'

if __name__ == '__main__':
    pprint(weather('hubert'))
    pprint(weather('jacksonville,nc'))
    pprint(weather())
    pprint(weather('kjasfklewrmndzkljf'))
