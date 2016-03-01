import aiohttp
import asyncio
import logging
import discord
from discord.ext import commands

from config.credentials import LOGIN_EMAIL, LOGIN_PASS
import modules.ballotbox
import modules.fweight
import modules.time
import modules.who

ALLIANCE = 99002172
#ALLIANCE = 1354830081
VALUE = 100000000
BIGVALUE = 25000000000

bot = commands.Bot(command_prefix='!', description='Rooster knows all...')

@bot.command(description="Get's the current EVE Time")
async def time():
    '''
    Shows the current time in UTC (EVE TIME)

    Should probably add options, and formatting
    '''
    logging.info('Caught !time, sending')
    await bot.say(modules.time.time())


@bot.command(description = "info about a player.  name, age, sec status, stats, corp info, and last kb activity")
async def who(*toon: str):
    '''
    Basic Public info about a given EVE Character
    '''
    logging.info('Caught !who with paramaters: {}'.format(toon))
    toon = ' '.join(toon)
    info = modules.who.who(toon)
    await bot.say(info)


@bot.command(description="Get a user's contract status(es) from fweight (or totals if none given")
async def fweight(*toon: str):
    '''
    Status(es) of pending fweight contracts
    '''
    logging.info("Caught !fweight with paramaters: {}".format(toon))
    toon = ' '.join(toon)
    status = modules.fweight.fweight(toon)
    await bot.say(status)


@bot.command(pass_context=True, description="Call a vote for 30 seconds")
async def vote(ctx, *question : str):
    '''
    Call a vote for 30 seconds.  ex: !vote Is Chainsaw amazing?
    '''
    global bb
    if bb.alive():
        await bot.say('There is already a vote in progress, wait for current vote to end first...')
        return
    else:
        question = ' '.join(question).strip()
        msg = await bot.say('{} has called a vote!\n**{}**\nVoting enabled for 30 seconds!'.format(ctx.message.author.name, question))
        bb.started()
        await asyncio.sleep(30)
        await bot.edit_message(msg, '{} has called a vote!\n**{}**\nVoting has ended!!'.format(ctx.message.author.name, question))
        bb.stopped()
        yay, nay = bb.results()
        if yay > nay:
            await bot.say("Motion passes with {} votes for and {} against.".format(yay, nay))
        elif nay > yay:
            await bot.say("Motion fails with {} against and {} for.".format(nay, yay))
        else:
            await bot.say("Tied Vote!!  {} votes each".format(yay))
        bb.reset()


@bot.command(pass_context=True, description="Vote 'Yes' in an active vote.")
async def yes(ctx):
    '''
    Vote "Yes" in a running vote.
    '''
    global bb
    if bb.alive():
        if bb.has_voted(ctx.message.author.name):
            bb.voteyes()
            bb.voted(ctx.message.author.name)
    else:
        await bot.say("There is currently no vote in progress")


@bot.command(pass_context=True, description="Vote 'No' in an active Vote")
async def no(ctx):
    '''
    Vote "No" in a running vote.
    '''
    global bb
    if bb.alive():
        if bb.has_voted(ctx.message.author.name):
            bb.voteno()
            bb.voted(ctx.message.author.name)
    else:
        await bot.say("There is currently no vote in progress")

async def killwatch():
    await bot.wait_until_ready()

    channel = discord.utils.get(bot.get_all_channels(), name='alliance')
    if not channel:
        logging.warning('That Channel isnt on the server, killwatch not running')
        return

    #await bot.send_message(channel, "**KILL ALERT** is running! {:,}ISK Alliance Threshhold:{:,} Big isk Threshold <BETA>".format(VALUE, BIGVALUE))

    while not bot.is_closed:
        with aiohttp.ClientSession() as session:
            async with session.get('http://redisq.zkillboard.com/listen.php') as resp:
                stream = await resp.json()
        if stream['package']:
            if 'alliance' in stream['package']['killmail']['victim']:
                if stream['package']['killmail']['victim']['alliance']['id'] == ALLIANCE:
                    if stream['package']['zkb']['totalValue'] >= VALUE:
                        await bot.send_message(channel, "**VICTIM ALERT**\nhttps://zkillboard.com/kill/{}/".format(
                                                        stream['package']['killID']))
                        continue
            for attacker in stream['package']['killmail']['attackers']:
                if 'alliance' in attacker:
                    if attacker['alliance']['id'] == ALLIANCE:
                        if stream['package']['zkb']['totalValue'] >= VALUE:
                            await bot.send_message(channel, "**KILL ALERT**\nhttps://zkillboard.com/kill/{}/".
                                                            format(stream['package']['killID']))
                            break
            if stream['package']['zkb']['totalValue'] >= BIGVALUE:
                await bot.send_message(channel, "**BIG KILL ALERT**\nhttps://zkillboard.com/kill/{}/".
                                       format(stream['package']['killID']))

#Since we are the server owner, and auth gives us a new titleset everytime someone enables discord, this is an ugly
#hack to make sure we keep our amazing title and prestige on the server.  nofuks
async def give_admin():
    await bot.wait_until_ready()
    while bot.is_logged_in:
        logging.debug("Giving bot overlord title")
        server = discord.utils.get(bot.servers, name='J4LP')
        await bot.add_roles(discord.utils.get(bot.get_all_members(), name="Rooster"),
                            discord.utils.get(server.roles, name="Supreme Overlord"))
        await asyncio.sleep(1800)

@bot.event
async def on_ready():
    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.debug(bot.user.id)
    logging.debug('------')


loop = asyncio.get_event_loop()
bb = modules.ballotbox.Ballot_Box()

while True:
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    logging.info('bot isnt on, connecting')
    try:
        loop.create_task(killwatch())
        loop.create_task(give_admin())
        loop.run_until_complete(bot.run(LOGIN_EMAIL, LOGIN_PASS))
        # loop.run_forever(bot.run(LOGIN_EMAIL, LOGIN_PASS))
    except Exception:
        loop.run_until_complete(bot.close())
    finally:
        loop.close()
        bot.close()

