from itertools import islice
import requests

def price(item=None):
    if not item:
        return "Need something to price, dum dum"

    if item.lower() == 'plex':
        itemName = "30 Day Pilot's License Extension (PLEX)"
        itemid = 29668
    else:
        itemName, itemid = get_type_id(item)

    if itemid:
        prices = get_prices(itemid)
    else:
        searchitems = get_multiple_type_id(item)
        if searchitems:
            prices = ''
            for i in searchitems:
                prices = prices + searchitems[i] + format_price(get_prices(i)) + '\n'
            return prices[:-2]
        else:
            return "Item not found"

    return itemName + format_price(prices)

def get_type_id(item):
    fuzzapi = 'https://www.fuzzwork.co.uk/api/typeid.php?typename='
    r = requests.get(fuzzapi + item)
    r = r.json()
    if r['typeID'] > 0:
        return r['typeName'], r['typeID']
    else:
        return None, None


def get_multiple_type_id(item):
    searchurl = 'https://api.evehound.com/search/{}/1'
    r = requests.get(searchurl.format(item))
    result = r.json()
    marketitems = {}
    _ = 0
    for i in result:
        if i == 'searchInfo' or _ > 2:
            continue
        if result[i]['type'] == 'marketItem':
            marketitems[result[i]['itemTypeId']] = result[i]['itemName']
            _ += 1
    return marketitems


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
