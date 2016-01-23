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
        return "**{}**(Born {}) _{}_ {} - {}(Joined {}) of {}".format(name, age, secstatus, stats, corp, corpsince, alliance)
    else:
        return "**{}**(Born {}) _{}_ {} - {}(Joined {})".format(name, age, secstatus, stats, corp, corpsince)

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
        return '[N/A, N/A]'

    data = r.json()

    if not data:
        return '[0, 0]'

    try:
        kills = data["shipsDestroyed"]
        losses = data["shipsLost"]
    except:
        ''' FUCKING PANIC ON EVERY ERROR JESUS ZKILL '''
        return '[0, 0]'
    return '[{}, {}]'.format(kills, losses)

if __name__ == "__main__":
    proper = who('Chainsaw McGinny')
    case = who('chainsaw mcginny')
    bad = who('csawmcfly')

    print('{} with proper case and {} without'.format(proper, case))
    print('{} bad name'.format(bad))
