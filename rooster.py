import asyncio
import discord
import requests
from discord.ext import commands

from config.credentials import LOGIN_EMAIL, LOGIN_PASS
import modules.fweight
import modules.who

ALLIANCE = 99002172
#ALLIANCE = 1354830081
VALUE = 100000000

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


async def killwatch():
    await bot.wait_until_ready()
    chans = {}
    for i in bot.get_all_channels():
        chans[i.name] = i.id
    try:
        channel = discord.Object(id=chans['alliance'])
    except Exception:
        print('that channel isnt on the server, background task not running')
        return
    await asyncio.sleep(1)
    if not bot.is_closed:
        await bot.send_message(channel, "**KILL ALERT** is running! {:,}ISK Threshhold <BETA>".format(VALUE))
        while True:
            r = requests.get('http://redisq.zkillboard.com/listen.php')
            stream = r.json()
            try:
                for kill in stream:
                    if 'alliance' in stream[kill]['killmail']['victim']:
                        if stream[kill]['killmail']['victim']['alliance']['id'] == ALLIANCE:
                            if stream[kill]['zkb']['totalValue'] >= VALUE:
                                await bot.send_message(channel, "**KILL ALERT**\nhttps://zkillboard.com/kill/{}/".format(
                                                                stream[kill]['killID']))
                                break
                    for attacker in stream[kill]['killmail']['attackers']:
                        if 'alliance' in attacker:
                            if attacker['alliance']['id'] == ALLIANCE:
                                if stream[kill]['zkb']['totalValue'] >= VALUE:
                                    await bot.send_message(channel, "**KILL ALERT**\nhttps://zkillboard.com/kill/{}/".
                                                                    format(stream[kill]['killID']))
                                break
            except TypeError:
                continue
            await asyncio.sleep(5)


loop = asyncio.get_event_loop()

while True:
    if bot.is_logged_in:
        continue
    else:
        print('bot isnt on, connecting')
        try:
            loop.create_task(killwatch())

            loop.run_until_complete(bot.run(LOGIN_EMAIL, LOGIN_PASS))
        except Exception:
            loop.run_until_complete(bot.close())
        finally:
            loop.close()

