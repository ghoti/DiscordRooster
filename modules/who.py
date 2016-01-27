import arrow
import evelink.api
import evelink.corp
import evelink.eve
from html.parser import HTMLParser
import requests

from config.credentials import CORP_KEYID, CORP_VCODE


def who(toon):

    if not toon:
        return 'NEED A NAME WTF'

    api = evelink.eve.EVE()
    id = api.character_id_from_name(toon)

    if not id.result:
        return "Character not found"

    # There be dragons here
    try:
        # if this breaks, that means someone tried to who a corp, we can handle that
        name, corp, corpsince, alliance, secstatus, age = corpsheet(id, api)
        stats = killstats(id)

        if alliance:
            return "```{} (Born {})\n{} SecStatus with {}\nJoined {} {} ({})```".format(
                    name, age, secstatus, stats, corp, corpsince, alliance)
        else:
            return "```{} (Born {})\n{} SecStatus with {}\nJoined {} {}```".format(
                    name, age, secstatus, stats, corp, corpsince)
    except evelink.api.APIError:
        try:
            #and here we fail if we supplied an alliance name, oof
            name, ticker, alliance, desc, ceo, members = corpinfo(id)
            return "``` {} <{}>\n{}\nAlliance: {}\nCEO: {}\nMembers: {}```".format(name, ticker, desc, alliance, ceo, members)
        except evelink.api.APIError:
            return "Seems you supplied an alliance name, soonTM"





def corpsheet(id, api):
    info = api.character_info_from_id(id.result)
    name = info.result['name']
    corp = info.result['corp']['name']
    corpsince = arrow.get(info.result['corp']['timestamp']).humanize()
    alliance = info.result['alliance']['name']
    secstatus = float('%.2f' % info.result['sec_status'])
    age = arrow.get(info.result['history'][-1]['start_ts']).humanize()
    return name, corp, corpsince, alliance, secstatus, age


def corpinfo(id):
    api = evelink.api.API(api_key=(CORP_KEYID, CORP_VCODE))
    corp = evelink.corp.Corp(api=api)
    info = corp.corporation_sheet(corp_id=id.result)
    name = info.result['name']
    ticker = info.result['ticker']
    alliance = info.result['alliance']['name']
    desc = info.result['description']
    desc = strip_tags(desc)
    ceo = info.result['ceo']['name']
    members = info.result['members']['current']
    return name, ticker, alliance, desc, ceo, members


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


class MLStripper(HTMLParser):
    '''
    Simple, no nonsense, make things unpretty html stripper for descriptions
    '''
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

if __name__ == "__main__":
    proper = who('Chainsaw McGinny')
    case = who('chainsaw mcginny')
    bad = who('csawmcfly')

    print('{} with proper case and {} without'.format(proper, case))
    print('{} bad name'.format(bad))
