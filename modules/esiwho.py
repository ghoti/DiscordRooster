from discord import Embed, Color
from esipy import App, EsiClient
import pendulum
import requests


def who(esi_app, esi_client, toon=None):
    if not toon:
        return 'Need a name WTF'

    #esi_app = App.create('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')
    #esi_client = EsiClient()

    character = esi_app.op['get_search'](categories=['character', 'corporation'], search=toon, strict=True)

    char_id = esi_client.request(character)

    if 'character' in char_id.data:
        charid = char_id.data['character']
        name, corpid, allianceid, sec_status, age = character_sheet(esi_app, esi_client, charid)
        timeincorp = time_in_corp(esi_app, esi_client, charid, corpid)
        last_active = activity(charid)
        activitystring = killstats(charid)
        corpinfo = esi_app.op['get_corporations_corporation_id'](corporation_id=corpid)
        corpname = esi_client.request(corpinfo).data['corporation_name']
        if allianceid:
            allianceinfo = esi_app.op['get_alliances_alliance_id'](alliance_id=allianceid)
            alliancename = esi_client.request(allianceinfo).data['alliance_name']
        embed = Embed(type='rich')
        embed.color = Color.dark_orange()
        embed.set_author(name=name)
        embed.set_thumbnail(url='https://image.eveonline.com/Character/{}_256.jpg'.format(charid))
        embed.url = 'https://https://zkillboard.com/character/{}/'.format(name.replace(' ', '+'))
        if allianceid:
            embed.description = 'Born {}\nJoined {} ({}) {}\n{} Sec Status with {}\nLast active in game: {}'.format(
                age, corpname, alliancename, timeincorp, sec_status, activitystring, last_active)
        else:
            embed.description = 'Born {}\nJoined {} {}\n{} Sec Status with {}\nLast activity in game: {}'.format(
                age, corpname, timeincorp, sec_status, activitystring, last_active)
        return embed


    if 'corporation' in char_id.data:
        corpid = char_id.data['corporation']
        name, ticker, allianceid, members, age = corp_sheet(esi_app, esi_client, corpid)
        activitystring = corpstats(corpid)
        last_active = corpactivity(corpid)
        if allianceid:
            allianceinfo = esi_app.op['get_alliances_alliance_id'](alliance_id=allianceid)
            alliancename = esi_client.request(allianceinfo).data['alliance_name']
        embed = Embed(type='rich')
        embed.color = Color.dark_gold()
        embed.set_author(name=name + ' [' + ticker + ']')
        embed.set_thumbnail(url='https://image.eveonline.com/Corporation/{}_128.png'.format(corpid))
        embed.url = 'https://evewho.com/corp/{}'.format(name.replace(' ', '+'))
        if allianceid:
            embed.description = 'Founded {}\nMember of {}\nCurrent Members: {}\n{}\nLast active in game: {}'.format(
                age, alliancename, members, activitystring, last_active)
        else:
            embed.description = 'Founded {}\nCurrent Members: {}\n{}\nLast active in game: {}'.format(
                age, members, activitystring, last_active)
        return embed
    #maybe we come back to alliances
    #maybe we undiddle this and make seperate commands
    #maybe we go crazy
    if 'alliance' in char_id.data:
        return 'alliance found with id: {}'.format(char_id.data['alliance'])

    return 'Nothing found with that name.'


def character_sheet(esi_app, esi_client, charid):
    esiinfo = esi_app.op['get_characters_character_id'](character_id=str(charid))
    char_info = esi_client.request(esiinfo).data
    name = char_info['name']
    corp = char_info['corporation_id']
    try:
        alliance = char_info['alliance_id']
    except KeyError:
        alliance = None
    sec_status = float('%.2f' % char_info['security_status'])
    age = pendulum.parse(char_info['birthday'].to_json()).diff_for_humans()
    return name, corp, alliance, sec_status, age


def time_in_corp(esi_app, esi_client, charid, corpid):
    charhistory = esi_app.op['get_characters_character_id_corporationhistory'](character_id=str(charid))
    timeincorp = esi_client.request(charhistory)
    #first result _should_ be our current corp, assuming so until proven otherwise
    currentlength = pendulum.parse(timeincorp.data[0]['start_date'].to_json())
    return currentlength.diff_for_humans()


def time_in_alliance(esi_app, esi_client, corpid, allianceid):
    corphistory = esi_app.op['get_corporations_corporation_id_alliancehistory'](corporation_id=str(corpid))
    timeinalliance = esi_client.request(corphistory)
    for alliance in timeinalliance.data:
        if alliance['alliance_id'] == allianceid:
            currentlength = pendulum.parse(alliance['start_date'].to_json())
    return currentlength.diff_for_humans()

def corp_sheet(esi_app, esi_client, corpid):
    esiinfo = esi_app.op['get_corporations_corporation_id'](corporation_id=str(corpid))
    corp_info = esi_client.request(esiinfo).data
    name = corp_info['corporation_name']
    ticker = corp_info['ticker']
    members = corp_info['member_count']
    age = pendulum.parse(corp_info['creation_date'].to_json()).diff_for_humans()
    try:
        allianceid = corp_info['alliance_id']
    except KeyError:
        allianceid = None
    return name, ticker, allianceid, members, age


def activity(id):
    try:
        zkill = requests.get("https://zkillboard.com/api/kills/characterID/{}/".format(id), timeout=5)
        zkill = zkill.json()
        lastkill = pendulum.parse(zkill[0]['killTime']).diff_for_humans()
        #lastkill = arrow.get(zkill[0]['killTime'], 'YYYY-MM-DD HH:mm:ss')
        return lastkill
    except Exception as e:
        print(e)
        return "Never"


def corpactivity(id):
    try:
        zkill = requests.get("https://zkillboard.com/api/kills/corporationID/{}/".format(id), timeout=5)
        zkill = zkill.json()
        lastkill = pendulum.parse(zkill[0]['killTime']).diff_for_humans()
        #lastkill = arrow.get(zkill[0]['killTime'], 'YYYY-MM-DD HH:mm:ss')
        return lastkill
    except Exception as e:
        print(e)
        return "Never"


def killstats(id):
    '''
    Zkill is weird, so lots of try blocks to catch their weirdness
    '''

    try:
        r = requests.get('https://zkillboard.com/api/stats/characterID/{}/'.format(id), timeout=5)
    except TimeoutError:
        return '[ERROR AT ZKILL]'

    data = r.json()

    if not data:
        return ' no killboard data'

    try:
        kills = data["shipsDestroyed"]
        losses = data["shipsLost"]
    except KeyError:
        ''' FUCKING PANIC ON EVERY ERROR JESUS ZKILL '''
        return ' no reliable killboard data'

    return "{:,} kills and {:,} losses".format(kills, losses)


def corpstats(id):
    try:
        r = requests.get('https://zkillboard.com/api/stats/corporationID/{}/'.format(id), timeout=5)
    except TimeoutError:
        return '[ERROR AT ZKILL]'

    data = r.json()

    if not data:
        return ' no killboard data'

    try:
        kills = data["shipsDestroyed"]
        losses = data["shipsLost"]
    except KeyError:
        ''' FUCKING PANIC ON EVERY ERROR JESUS ZKILL '''
        return ' no reliable killboard data'

    return "{:,} kills and {:,} losses".format(kills, losses)