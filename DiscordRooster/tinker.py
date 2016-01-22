from discord.ext import commands

from config.credentials import LOGIN_EMAIL, LOGIN_PASS
import modules.who

bot = commands.Bot(command_prefix='!', description='Rooster knows all...')


@bot.command(description = "info about a player.  name, age, sec status, stats, and corp info")
async def who(*toon: str):
    '''
    Basic Public info about a given EVE Character
    '''
    toon = ' '.join(toon)
    info = modules.who.who(toon)
    await bot.say(info)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run(LOGIN_EMAIL, LOGIN_PASS)
