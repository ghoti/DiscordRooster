from discord.ext import commands

from config.credentials import LOGIN_EMAIL, LOGIN_PASS
import modules.fweight
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

@bot.command(description="Get a user's contract status(es) from fweight (or totals if none given")
async def fweight(*toon: str):
    '''
    Status(es) of pending fweight contracts
    '''
    toon = ' '.join(toon)
    status = modules.fweight.fweight(toon)
    await bot.say(status)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

while True:
    try:
        bot.run(LOGIN_EMAIL, LOGIN_PASS)
    except:
        print("Bot killed connection, restarting")
