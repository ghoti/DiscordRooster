#! /usr/bin/env python3
import asyncio
import logging
import operator
import re
import shelve
import datetime
from html.parser import HTMLParser
from time import sleep

import aiohttp
import arrow
import dateparser
import discord
import requests
import socket
import websockets
from discord.ext import commands
from esipy import EsiClient, App
from fuzzywuzzy import fuzz

import modules.ballotbox
import modules.buyback
import modules.esiwho
import modules.fweight
import modules.insurance
import modules.ly
import modules.newweather
import modules.time
import modules.weather
import modules.who
from config.credentials import LOGIN_TOKEN
from modules import kill

ALLIANCE = 1900696668
# ALLIANCE = 99002172
# ALLIANCE = 1354830081
global gameactive
gameactive = False

FIT_PARSE = re.compile('\[.+?, .+]')
OSMIUM_URL = 'https://o.smium.org/api/json/loadout/eft/attributes/loc:ship,a:tank,a:ehpAndResonances,a:capacitors,a:damage,a:priceEstimateTotal?input={}'
esi_app = App.create('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')
esi_client = EsiClient()

bot = commands.Bot(command_prefix='!', description='Rooster knows all...')
@bot.check
def can_speak(ctx):
    for i in ctx.message.author.roles:
        if i.name == 'Time-OUT':
            return False
    return True

@bot.command(pass_context=True, description="Change the MOTD of a channel")
@commands.has_any_role("Director")
async def topic(ctx, *motd: str):
    '''
    Director and above only.  Set the topic for the current room.
    '''
    motd = ' '.join(motd)
    await bot.edit_channel(channel=ctx.message.channel, topic=motd)
    await bot.say('{} has changed the topic to _{}_'.format(ctx.message.author.name, motd))


@bot.command(pass_context=True, description='Mute a given user')
@commands.has_any_role("Director", "OG")
async def mute(ctx, user: discord.Member):
    '''
    Director and above only.  Place @user into a special group that cannot participate in chats.
    '''
    server = ctx.message.server
    await bot.add_roles(user, discord.utils.get(server.roles, name="Time-OUT"))


@bot.command(pass_context=True, description='Unmute a given user')
@commands.has_any_role("Director", "OG")
async def unmute(ctx, user: discord.Member):
    '''
    Director and above only.  Unmute a @user to remove their special group and allow them to participate in chat again.
    '''
    server = ctx.message.server
    await bot.remove_roles(user, discord.utils.get(server.roles, name='Time-OUT'))

@bot.listen('on_reaction_add')
async def on_reaction_add(react, user):
    if user == bot.user:
        return
    if discord.utils.get(user.roles, name='Time-OUT'):
        await bot.remove_reaction(message=react.message, emoji=react.emoji, member=user)

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


@bot.command(description='New weather!', pass_context=True)
async def weather(ctx, *city: str):
    '''
    Get the weather at a specified city, or at ccp's home office if none provided.
    '''
    await bot.send_typing(destination=ctx.message.channel)
    city = ' '.join(city)
    weather = modules.newweather.weather(city)
    if type(weather) is discord.Embed:
        await bot.send_message(ctx.message.channel, embed=weather)
    else:
        await bot.say(weather)


@bot.command(description="Get's the current EVE Time")
async def time():
    '''
    Shows the current time in UTC (EVE TIME)

    Should probably add options, and formatting
    '''
    logging.info('Caught !time, sending')
    await bot.say(modules.time.time())


@bot.command(pass_context=True, description='Info about a character or corp if found')
async def who(ctx, *toon: str):
    '''
    Get basic, public info on a give eve character name. !who chainsaw mcginny
    '''
    await bot.send_typing(destination=ctx.message.channel)
    toon = ' '.join(toon)
    embed = modules.esiwho.who(esi_app, esi_client, toon)
    if type(embed) is discord.Embed:
        await bot.send_message(ctx.message.channel, embed=embed)
    else:
        await bot.say(embed)


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
        question = question.replace('@', '')
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
@commands.has_any_role('Director', 'OG')
async def mutekills():
    '''
    Director and above only.  Mute Roosters Killwatch function in the event of a zkill error or oppresive spam.
    Call again to allow killposting from rooster.
    '''
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
    # aiohttp doesnt bundle certs, ubuntu doesn't like using aiohttp, shits weird and nothing sensitive is being passed
    myconnecter = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=False)
    session = aiohttp.ClientSession(connector=myconnecter)
    while not bot.is_closed:
        try:
            async with session.get('https://redisq.zkillboard.com/listen.php') as resp:
                stream = await resp.json()
        except Exception as e:
            logging.warning('Killwatch server gave up on us', e)
            stream['package'] = None
            #just in case something is funny, let's close the session, go night night, and start over
            session.close()
            await asyncio.sleep(10)
            session = aiohttp.ClientSession(connector=myconnecter)
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
    '''
    Play Trivia!  Only available in #trivia (see auth groups for more info)
    '''
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

            await asyncio.sleep(2)

    with shelve.open('triviastats') as stats:
        statstring = '```Top 5 after this round:\n'
        for x in sorted(stats.items(), key=operator.itemgetter(1), reverse=True)[:5]:
            statstring = statstring+'{} : {} Correct\n'.format(x[0], x[1])
        await bot.say(statstring+'```')
        await asyncio.sleep(1)
        await bot.say('!trivia for a new round!')
        gameactive = False


@bot.command(pass_context=True, description='Give trivia stats for user')
async def stats(ctx):
    '''
    Give a user their trivia stats
    '''
    with shelve.open('triviastats') as stats:
        if ctx.message.author.name in stats:
            await bot.say("{} has correctly answered {} Trivia Question in #trivia".format(
                ctx.message.author.name, stats[ctx.message.author.name]
            ))
        else:
            await bot.say("{} Has not answered any Trivia Questions in #trivia".format(ctx.message.author.name))


@bot.command(pass_context=True, description='Remind user <message> in <time given>')
async def remind(ctx, *reminder):
    '''
    Usage: !remind [time] - [message]
    Can parse a lot of human readable and date specific time frames, but it's not perfect.
    example !remind in 1 hour - tell chainsaw he is amazing, !remind 12 hours - chainsaw is still amazing

    To delete a reminder before it occurs, call !myreminders to get the id and call !remind delete <id> or
    !remind delete all to purge all reminders for yourself in the current channel.
    '''
    if not reminder:
        #im lazy and getting the docstring is not worth my time :colbert:
        await bot.say("```Usage: !remind [time] - [message]\n\nCan parse a lot of human readable and date \
                       specific time frames, but it's not perfect.\n\nExample: !remind in 1 hour - tell chainsaw he \
                        is amazing, !remind 12 hours - chainsaw is still amazing```")
        return

    reminder = ' '.join(reminder).strip()
    if reminder.lower().startswith('delete'):
        item = reminder.split()[1]
        with shelve.open('reminders') as reminders:
            if item == 'all':
                for i in reminders.keys():
                    remindtime, author, message, channel = reminders[i]
                    print(author, channel)
                    if ctx.message.author.id == author and ctx.message.channel.id == channel.id:
                        del reminders[i]
                await bot.say("OK, all your reminders for this channel have been purged!")
                return
            try:
                timer, author, message, channel = reminders[item]
            #ignore a keyerror, if someone tries to delete something that aint there, idgaf
            except KeyError:
                return
            if ctx.message.author.id == author and ctx.message.channel.id == channel.id:
                del reminders[item]
                await bot.say("OK.  I wont remind you about that any more.")
        return

    time, message = reminder.split(' - ')
    if len(message) > 200:
        await bot.say('Reminder too long, try again with something shorter.  Sorry.')
        return

    #the james/shlomo fix.
    message = message.replace('@everyone', 'everyone')
    message = message.replace('@here', 'here')

    remindtime = dateparser.parse(time, settings={'TIMEZONE': 'UTC', 'PREFER_DATES_FROM': 'future'})
    now = datetime.datetime.utcnow()

    logging.info('parsed time as {}'.format(remindtime))
    if not remindtime:
        await bot.say('Whoops, seems you supplied an invalid time for this reminder, try something like, in 1 hour, '
                      '1day 12hours, 2017-12-25 00:00:00, 01:00...')
        return

    #if the user enters something and we parse it as already past, assume the future - cuz you know.. remind..
    #this gets weird with some values, i've come to the realization that it's just gonna be accepted if a user tries
    #to put in a time in the past, that they instead get reminded in the future.  dealwithit.jpg
    #Thanks Sergei for the help on this bit
    if remindtime <= now:
        logging.info('event is in the past, moving forward')
        future = now - remindtime
        #time time waits for no man
        remindtime = remindtime + future + future

    if remindtime > now:
        with shelve.open('reminders') as reminders:
            #limit reminders to 10, lets check here
            counter = 0
            for item in reminders.keys():
                if ctx.message.author.id in reminders[item]:
                    counter = counter + 1
            if counter > 10:
                await bot.say("Sorry, you've hit the limit of reminders (10)")
                return
            reminders[str(len(reminders)+1)] = [remindtime, ctx.message.author.id, message, ctx.message.channel]
        await bot.say("Okey Dokey <@{}>, I'll remind you about that at **{}**".format(ctx.message.author.id,
                                                                             remindtime.strftime("%Y-%m-%d %H:%M:%S")))
        return

    #this, in theory, should be unreachable.  watch me be wrong at some point.
    else:
        await bot.say('This is in the past, {}'.format(remindtime.strftime("%Y-%m-%d %H:%M:%S")))


@bot.command(pass_context=True, description='Show your current reminders')
async def myreminders(ctx):
    '''
    Shows a list of your pending reminders for the current channel.
    To delete a reminder use !remind delete <id> shown below or !remind delete all to remove all reminders for the
    current channel.
    '''
    with shelve.open('reminders') as reminders:
        totalreminders = discord.Embed()
        minder = ''
        for item in reminders.keys():
            logging.info("{}, {}".format(item, reminders[item]))
            if ctx.message.author.id in reminders[item]:
                timer, author, message, channel = reminders[item]
                if channel.id == ctx.message.channel.id:
                    minder = minder + '{}. {}\n'.format(item, message)
        totalreminders.description = minder
        totalreminders.set_author(name=ctx.message.author)
    await bot.say(embed=totalreminders)


async def remindqueue():
    logging.info('reminder q started')
    while True:
        with shelve.open('reminders') as reminders:
            for item in reminders.keys():
                remindtime, author, message, channel = reminders[item]
                if datetime.datetime.utcnow() > remindtime:
                    await bot.send_message(destination=channel, content='Hey, <@{}>! {}'.format(author, message))
                    del reminders[item]
        await asyncio.sleep(10)


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
        loop.create_task(remindqueue())
        loop.run_until_complete(bot.connect())




    except (discord.HTTPException, aiohttp.ClientError, discord.GatewayNotFound,
            websockets.InvalidHandshake, websockets.WebSocketProtocolError):
        logging.exception("Discord.py pls")
        loop.run_until_complete(sleep(10))
