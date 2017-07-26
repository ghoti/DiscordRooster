from darksky import forecast
from discord import Embed, Color
import googlemaps

from config.credentials import GOOGLEKEY, DARKKEY

def weather(city=None):
    if not city:
        return weather('Reykjavik')

    gmaps = googlemaps.Client(key=GOOGLEKEY)
    address = gmaps.geocode(city)

    if not address:
        return 'No city or location found with that name, try again?'


    lat = address[0]['geometry']['location']['lat']
    lng = address[0]['geometry']['location']['lng']


    with forecast(DARKKEY, lat, lng) as fore:
        embed = Embed(type='rich')
        condition = weather_condition_image(fore.currently.icon)
        embed.set_thumbnail(url=condition)
        embed.title = address[0]['formatted_address']
        embed.url = "https://darksky.net/forecast/{},{},".format(lat, lng)
        #embed.set_footer(text='Powered by Dark Sky', icon_url='https://darksky.net/images/darkskylogo.png')
        embed.description = fore.daily.summary
        #embed.add_field(name='Daily Summary:', value=fore.daily.summary)
        embed.add_field(name='Current Conditions:', value='{}\n{}F/{:.1f}C (feels like {}F/{:.1f}C) at {}% Humidity'.format(
            fore.currently.summary, fore.currently.temperature, (fore.currently.temperature-32)*(5/9),
            fore.currently.apparentTemperature, (fore.currently.apparentTemperature-32)*(5/9), int(fore.currently.humidity*100)))

        if hasattr(fore, 'alerts'):
            embed.color = Color.red()
            for alert in fore.alerts:
                embed.add_field(name=alert['severity'], value=alert['title'], inline=False)
                #embed.description = embed.description + '\n{}'.format(alert['title'])
        return embed

def weather_condition_image(condition):
    '''
    icons for weather thanks to https://www.dr-lex.be/software/darksky-icons.html
    uploaded to imgur for hardcoded goodness
    '''
    if condition == 'clear-day': return 'http://i.imgur.com/ebBKojX.png'
    if condition == 'clear-night': return 'http://i.imgur.com/OZ2bhJw.png'
    if condition == 'rain': return 'http://i.imgur.com/ZxYcTvw.png'
    if condition == 'snow': return 'http://i.imgur.com/q1r67Lz.png'
    if condition == 'sleet': return 'http://i.imgur.com/0NG3rKH.png'
    if condition == 'wind': return 'http://i.imgur.com/88CjA2l.png'
    if condition == 'fog': return 'http://i.imgur.com/ZqMpsQ6.png'
    if condition == 'cloudy': return 'http://i.imgur.com/cbvq4Si.png'
    if condition == 'partly-cloudy-day': return 'http://i.imgur.com/SlGJVoL.png'
    if condition == 'partly-cloudy-night': return 'http://i.imgur.com/J4Y1VgH.png'



if __name__ == '__main__':
    print(weather().to_dict())
    print(weather('hubert nc').to_dict())
    print(weather(28584).to_dict())
    print(weather('la jolle').to_dict())
    print(weather('2lasdhjflnzxcfsadf'))