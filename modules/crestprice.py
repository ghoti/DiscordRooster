from fuzzywuzzy import fuzz, process
import requests
import pycrest


def price(item=None):
    if not item:
        return "Need something to price, dum dum"

    if item.lower() == 'plex':
        itemName = "30 Day Pilot's License Extension (PLEX)"
        itemid = 29668
    else:
        itemid, itemName = get_type_id(item)

    if itemid:
        prices = get_prices(itemid)
    else:
        return "Item not found"

    return itemName + format_price(prices)


def getByAttrVal(objlist, attr, val):
    ''' Searches list of dicts for a dict with dict[attr] == val '''
    matches = [getattr(obj, attr) == val for obj in objlist]
    index = matches.index(True)  # find first match, raise ValueError if not found
    return objlist[index]


def getAllItems(page):
    ''' Fetch data from all pages '''
    ret = page().items
    while hasattr(page(), 'next'):
        page = page().next()
        ret.extend(page().items)
    return ret

def get_type_id(item):
    eve = pycrest.EVE()
    eve()
    itemType = {}

    items = getAllItems(eve.itemTypes)
    for _ in items:
        d = _._dict
        itemType[d['id_str']] = d['name']

    for k, v in itemType.items():
        if fuzz.ratio(v.lower(), item.lower()) > 85:
            print(v, item)
            return k, v

def get_prices(itemid):
    #jita for now
    evecentral = 'http://api.eve-central.com/api/marketstat/json?typeid={}&usesystem=30000142'

    r = requests.get(evecentral.format(itemid))
    r = r.json()
    return r[0]

def format_price(data):
    return '  Sell: {:,}  Buy: {:,}  Volume: {}'.format(data['sell']['min'], data['buy']['max'], data['all']['volume'])

if __name__ == '__main__':
    print(price('plex'))
    print(price())
    print(price('stabber'))
    print(price('jacket'))
    print(price('fjasdknek'))







