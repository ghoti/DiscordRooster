#! /usr/bin/env python3
import asyncio
import logging
import operator
import re
import shelve
from datetime import timedelta
from html.parser import HTMLParser
from time import sleep

import aiohttp
import arrow
import discord
import requests
import websockets
from discord.ext import commands
from fuzzywuzzy import fuzz

import modules.ballotbox
import modules.buyback
import modules.fweight
import modules.insurance
import modules.ly
import modules.quote
import modules.time
import modules.weather
import modules.who
from config.credentials import LOGIN_TOKEN
from modules import quote, kill

ALLIANCE = 1900696668
# ALLIANCE = 99002172
# ALLIANCE = 1354830081
VALUE = 500000000
BIGVALUE = 20000000000
global gameactive
gameactive = False

FIT_PARSE = re.compile('\[.+?, .+]')
OSMIUM_URL = 'https://o.smium.org/api/json/loadout/eft/attributes/loc:ship,a:tank,a:ehpAndResonances,a:capacitors,a:damage,a:priceEstimateTotal?input={}'

bot = commands.Bot(command_prefix='!', description='Rooster knows all...')


@bot.command(pass_context=True, description="Change the MOTD of a channel")
@commands.has_any_role("Director", "Leadership")
async def topic(ctx, *motd: str):
    motd = ' '.join(motd)
    await bot.edit_channel(channel=ctx.message.channel, topic=motd)
    await bot.say('{} has changed the topic to _{}_'.format(ctx.message.author.name, motd))


@bot.command(pass_context=True, description='Mute a given user')
@commands.has_any_role("Director", "Leadership", "RetiredLeadership")
async def mute(ctx, user: discord.Member):
    server = ctx.message.server
    await bot.add_roles(user, discord.utils.get(server.roles, name="Time-OUT"))


@bot.command(pass_context=True, description='Unmute a given user')
@commands.has_any_role("Director", "Leadership", "RetiredLeadership")
async def unmute(ctx, user: discord.Member):
    server = ctx.message.server
    await bot.remove_roles(user, discord.utils.get(server.roles, name='Time-OUT'))


@bot.listen('on_message')
async def on_message(message):
    if message.author == bot.user:
        return
    if discord.utils.get(message.author.roles, name='Time-OUT'):
        await bot.delete_message(message)

    if re.match(FIT_PARSE, message.content):
        eft = re.search('\[(?P<SHIP>.+?), (?P<NAME>.+)]', message.content)
        name = eft.group('NAME')
        ship = eft.group('SHIP')
        r = requests.get(OSMIUM_URL.format(message.content), timeout=5)
        try:
            stats = ''
            fit = r.json()
            stats += '```Basic stats for {} - {} (ALL V\'s)\n'.format(ship, name)
            stats += 'Expected EHP (omni): {:,.2f}\n'.format(fit['ship']['ehpAndResonances']['ehp']['avg'])
            if fit['ship']['capacitors']['local']['stable']:
                stats += 'Cap Stable!\n'
            else:
                cap = timedelta(milliseconds=fit['ship']['capacitors']['local']['depletion_time'])
                stats += 'Expected cap time: {}\n'.format(cap)
            stats += 'Expected DPS/Volley: {:.2f}/{:.2f}\n'.format(fit['ship']['damage']['total']['dps'],
                                                                   fit['ship']['damage']['total']['volley'])
            stats += 'Estimated cost: {:,.2f}```'.format(
                fit['ship']['priceEstimateTotal']['ship'] + fit['ship']['priceEstimateTotal']['fitting'])
            await bot.send_message(destination=message.channel, content=stats)
        except Exception as e:
            print(e)
            pass


@bot.command(description="Get's the current weather as a city, or in CCP's office if none provided")
async def weather(*city: str):
    '''
    Get the weather in a specified city, or nearest weather station
    '''
    logging.info('Caught weather')
    city = ' '.join(city)
    weather = modules.weather.weather(city)
    await bot.say(weather)


@bot.command(description="Get's the current EVE Time")
async def time():
    '''
    Shows the current time in UTC (EVE TIME)

    Should probably add options, and formatting
    '''
    logging.info('Caught !time, sending')
    await bot.say(modules.time.time())


@bot.command(pass_context=True, description="info about a player.  name, age, sec status, stats, corp info, and last kb activity")
async def who(ctx, *toon: str):
    '''
    Basic Public info about a given EVE Character
    '''
    await bot.send_typing(destination=ctx.message.channel)
    logging.info('Caught !who with paramaters: {}'.format(toon))
    toon = ' '.join(toon)
    info = modules.who.who(toon)
    await bot.say(info)


@bot.command(pass_context=True, description="Get a user's contract status(es) from fweight (or totals if none given")
async def fweight(ctx, *toon: str):
    '''
    Status(es) of pending fweight contracts
    '''
    await bot.send_typing(destination=ctx.message.channel)
    logging.info("Caught !fweight with paramaters: {}".format(toon))
    toon = ' '.join(toon)
    status = modules.fweight.fweight(toon)
    await bot.say(status)

@bot.command(pass_context=True, description="Get number of outstanding buyback contracts")
async def buyback(ctx):
    await bot.send_typing(destination=ctx.message.channel)
    status = modules.buyback.buyback()
    await bot.say(status)

@bot.command(description="Gets distance and required JDC level information for jumping between two systems")
async def ly(*systems: str):
    systems = ' '.join(systems)
    status = modules.ly.ly(systems)
    await bot.say(status)

@bot.command(pass_context=True, description="Get Platinum insurance rate for a ship")
async def insure(ctx, *ship: str):
    '''
    Insurance rate (platinum) for a given ship
    '''
    await bot.send_typing(destination=ctx.message.channel)
    logging.info("Caught !insure with paramaters: {}".format(ship))
    ship = ' '.join(ship)
    insurance = modules.insurance.insure(ship)
    await bot.say(insurance)


@bot.command(pass_context=True, description="Call a vote for 30 seconds")
async def vote(ctx, *question: str):
    '''
    Call a vote for 30 seconds.  ex: !vote Is Chainsaw amazing?
    '''
    global bb
    if bb.alive():
        await bot.say('There is already a vote in progress, wait for current vote to end first...')
        return
    else:
        question = ' '.join(question).strip()
        msg = await bot.say(
            '{} has called a vote!\n**{}**\nVoting enabled for 30 seconds!'.format(ctx.message.author.name, question))
        bb.started()
        await asyncio.sleep(30)
        await bot.edit_message(msg, '{} has called a vote!\n**{}**\nVoting has ended!!'.format(ctx.message.author.name,
                                                                                               question))
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

@bot.command(pass_context=True, description="Mute Roosters Kill announcer")
@commands.has_any_role('Director', 'RetiredLeadership')
async def mutekills():
    global killwatchmute
    if killwatchmute:
        killwatchmute = False
        await bot.say("Killwatching resumed.")
    else:
        killwatchmute = True
        await bot.say("Killwatching suppressed.")


async def killwatch():
    await bot.wait_until_ready()
    global killwatchmute
    killwatchmute = False

    channels = []
    for chan in bot.get_all_channels():
        if chan.name == 'fweddit':
            channels.append(chan)
    if not channels:
        logging.warning('no channels for kill announcing, killwatch not running')
        return
    logging.info('killwatch alive on the following servers:')
    logging.info(bot.servers)
    # for channel in channels:
    # await bot.send_message(channel, "**KILL ALERT** is running! {:,}ISK Alliance Threshhold:{:,} Big isk Threshold <BETA>".format(VALUE, BIGVALUE))

    while not bot.is_closed:
        try:
            with aiohttp.ClientSession() as session:
                async with session.get('http://redisq.zkillboard.com/listen.php') as resp:
                    stream = await resp.json()
        except Exception:
            logging.warning('Killwatch server gave up on us')
            await asyncio.sleep(10)
            stream['package'] = None
        if stream['package'] and not killwatchmute:
            currentkill = kill.Kill(stream)
            if currentkill.isOldKill():
                continue
            if currentkill.victimAlliance() and currentkill.isValuable():
                for channel in channels:
                    await bot.send_message(channel, "**VICTIM ALERT**\nhttps://zkillboard.com/kill/{}/".format(
                        currentkill.killid))
                continue
            if currentkill.attackerAlliance() and currentkill.isValuable():
                for channel in channels:
                    await bot.send_message(channel, "**KILL ALERT**\nhttps://zkillboard.com/kill/{}/".format(
                        currentkill.killid))
                continue
            if currentkill.isBigKill():
                for channel in channels:
                    await bot.send_message(channel, "**BIG KILL ALERT**\nhttps://zkillboard.com/kill/{}/".format(
                        currentkill.killid))
                continue
        #just in case we hit a rate limit while parsing a fight or something silly
        await asyncio.sleep(2)

@bot.command(pass_context=True, description="Start a round of Trivia!")
async def trivia(ctx):
    global gameactive
    if gameactive:
        return
    if ctx.message.channel.name != "trivia":
        await bot.say("Trivia not allowed here, try again in the #trivia channel!")
        return
    class MLStripper(HTMLParser):
        '''
        Simple, no nonsense, make things unpretty html stripper for descriptions
        '''

        def __init__(self):
            super().__init__()
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.fed = []

        def handle_data(self, d):
            self.fed.append(d)

        def get_data(self):
            return ''.join(self.fed)

    def strip_tags(html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    #stats = shelve.open('triviastats')
    streak = 0
    gameactive = True

    while streak < 5:
        try:
            with aiohttp.ClientSession() as session:
                async with session.get('http://jservice.io/api/random') as resp:
                    stream = await resp.json()
        except:
            await bot.say("Trivia is currently down. Try again in a bit.")
            return
        timer = arrow.utcnow().replace(seconds=30)
        if stream and stream[0]['question']:
            if stream[0]['invalid_count']:
                await bot.say('Invalid Question fetched, aborting round.')
                break
            answer = strip_tags(stream[0]['answer'])
            msg = await bot.say('Category: {}  Value: ${}\nQuestion: {}'.format(
                                             stream[0]['category']['title'], stream[0]['value'], stream[0]['question']))
            bar = '=============================='
            visual = await bot.say(bar)
            while True:
                guess = await bot.wait_for_message(timeout=1)

                if timer < arrow.utcnow():
                    await bot.delete_message(visual)
                    await bot.say("No one guessed the correct answer: {}".format(answer))
                    streak = streak + 1
                    break
                if guess:
                    if fuzz.ratio(guess.content.lower(), answer.lower()) >= 80:
                        await bot.delete_message(visual)
                        await bot.say('Ding! {} guessed the correct answer: {}'.format(guess.author.name, answer))
                        with shelve.open('triviastats') as stats:
                            if guess.author.name in stats:
                                stats[guess.author.name] += 1
                            else:
                                stats[guess.author.name] = 1
                        streak = streak + 1
                        break
                bar = bar[:-1]
                if len(bar) % 5 == 0:
                    visual = await bot.edit_message(visual, bar)

            await asyncio.sleep(1)

    with shelve.open('triviastats') as stats:
        statstring = '```Top 5 after this round:\n'
        for x in sorted(stats.items(), key=operator.itemgetter(1), reverse=True)[:5]:
            statstring = statstring+'{} : {} Correct\n'.format(x[0], x[1])
        await bot.say(statstring+'```')
        await asyncio.sleep(1)
        await bot.say('!trivia for a new round!')
        gameactive = False


@bot.command(description="Grabs or stores a quote from discord.")
async def q(*quote_key: str):
    await bot.wait_until_ready()
    try:
        key = quote_key[0]
    except IndexError:
        await bot.say("You will have to give me a key to be funny.")
        return

    logging.info("posted a quote, key {}".format(key))
    resp = quote.get_quote(key)
    await bot.say(resp)


@bot.command(description="Remembers a quote")
async def remember(*input: str):
    await bot.wait_until_ready()
    try:
        key = input[0]
        value = ' '.join(input[1:])
    except IndexError:
        await bot.say("Not enough to make a quote.")
        return

    logging.info("Storing quote, key: '{}', value: '{}'".format(key, value))
    quote.store_quote(key, value)
    await bot.say("Got it.")


@bot.command(description="Forgets a key in the quote list.")
async def forget(*input: str):
    await bot.wait_until_ready()
    try:
        key = input[0]
        quote.delete_quote(key)
        await bot.say("k.")
    except IndexError:
        await bot.say("I will not have blanket amnesia, thank you.")


@bot.command(description="Lists all possible quote keys, but not the values.")
async def quotes():
    await bot.wait_until_ready()
    await bot.say(quote.get_key_list())


@bot.event
async def on_ready():
    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.debug(bot.user.id)
    logging.debug('------')
    await bot.change_presence(game=discord.Game(name="a game of Chicken"))


bb = modules.ballotbox.Ballot_Box()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logging.info('bot isnt on, connecting')
loop = asyncio.get_event_loop()

while True:
    try:
        task = bot.login(LOGIN_TOKEN)
        loop.run_until_complete(task)


    except (discord.HTTPException, aiohttp.ClientError):
        logging.exception("Discord.py pls")
        loop.run_until_complete(sleep(10))

    else:
        break

while not bot.is_closed:
    try:
        logging.info('starting our tasks')
        loop.create_task(killwatch())
        loop.run_until_complete(bot.connect())




    except (discord.HTTPException, aiohttp.ClientError, discord.GatewayNotFound,
            websockets.InvalidHandshake, websockets.WebSocketProtocolError):
        logging.exception("Discord.py pls")
        loop.run_until_complete(sleep(10))
