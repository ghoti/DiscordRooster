import arrow
import evelink.eve
import requests

def who(toon):

    if not toon:
        return("NEED A NAME WTF")

    api = evelink.eve.EVE()
    id = api.character_id_from_name(toon)

    if not id.result:
        return "Character not found"

    name, corp, corpsince, alliance, secstatus, age = corpsheet(id, api)
    stats = killstats(id)

    if alliance:
        return "```{} (Born {})\n{} SecStatus with {}\nJoined {} {} ({})```".format(
                name, age, secstatus, stats, corp, corpsince, alliance)
    else:
        return "```{} (Born {})\n{} SecStatus with{}\nJoined {} {}```".format(name, age, secstatus, stats, corp, corpsince)

def corpsheet(id, api):
    info = api.character_info_from_id(id.result)
    name = info.result['name']
    corp = info.result['corp']['name']
    corpsince = arrow.get(info.result['corp']['timestamp']).humanize()
    alliance = info.result['alliance']['name']
    secstatus = float('%.2f' % info.result['sec_status'])
    age = arrow.get(info.result['history'][-1]['start_ts']).humanize()
    return name, corp, corpsince, alliance, secstatus, age

def killstats(id):
    '''
    Zkill is weird, so lots of try blocks to catch their weirdness
    '''

    try:
        r = requests.get('https://zkillboard.com/api/stats/characterID/{}/'.format(id.result), timeout=10)
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

    return "{} kills and {} losses".format(kills, losses)

if __name__ == "__main__":
    proper = who('Chainsaw McGinny')
    case = who('chainsaw mcginny')
    bad = who('csawmcfly')

    print('{} with proper case and {} without'.format(proper, case))
    print('{} bad name'.format(bad))
