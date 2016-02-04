import asyncio
import discord
import requests
from discord.ext import commands

from config.credentials import LOGIN_EMAIL, LOGIN_PASS
import modules.fweight
import modules.time
import modules.who

ALLIANCE = 99002172
#ALLIANCE = 99002775
VALUE = 100000000

bot = commands.Bot(command_prefix='!', description='Rooster knows all...')

@bot.command(description="Get's the current EVE Time")
async def time():
    '''
    Shows the current time in UTC (EVE TIME)

    Should probably add options, and formatting
    '''
    await bot.say(modules.time.time())


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
    while not bot.is_closed:
        await asyncio.sleep(5)
        #await bot.send_message(channel, "**KILL ALERT** is running! {:,}ISK Threshhold <BETA>".format(VALUE))
        try:
            r = requests.get('http://redisq.zkillboard.com/listen.php')
            stream = r.json()
        except Exception:
            continue
        if stream['package']:
            #for kill in stream['package']:
            if 'alliance' in stream['package']['killmail']['victim']:
                if stream['package']['killmail']['victim']['alliance']['id'] == ALLIANCE:
                    if stream['package']['zkb']['totalValue'] >= VALUE:
                        await bot.send_message(channel, "**KILL ALERT**\nhttps://zkillboard.com/kill/{}/".format(
                                                        stream['package']['killID']))
                        break
            for attacker in stream['package']['killmail']['attackers']:
                if 'alliance' in attacker:
                    if attacker['alliance']['id'] == ALLIANCE:
                        if stream['package']['zkb']['totalValue'] >= VALUE:
                            await bot.send_message(channel, "**KILL ALERT**\nhttps://zkillboard.com/kill/{}/".
                                                            format(stream['package']['killID']))
                            break

loop = asyncio.get_event_loop()

while True:
    if bot.is_logged_in:
        continue
    else:
        print('bot isnt on, connecting')
        try:
            loop.create_task(killwatch())
            loop.run_until_complete(bot.run(LOGIN_EMAIL, LOGIN_PASS))
            #loop.run_forever(bot.run(LOGIN_EMAIL, LOGIN_PASS))
        except Exception:
            loop.run_until_complete(bot.close())
        except:
            loop.run_until_complete(bot.close())
        finally:
            loop.close()
            bot.close()

