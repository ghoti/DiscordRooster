import arrow
import requests
import shelve

CREST_INSURANCE = 'https://crest-tq.eveonline.com/insuranceprices/'
INSURANCE_CACHETIMER = 3600

def insure(ship=None):
    if not ship:
        return 'NEED SHIP TO INSURE PLS'
    now = arrow.utcnow()
    shelfrates = shelve.open('insurance')

    if not 'cache' in shelfrates.keys():
        shelfrates['cache'] = now.replace(seconds=-1)

    if now > shelfrates['cache']:
        print('cache expired fetching new insurance rates')

        crestrates = requests.get(CREST_INSURANCE)

        #grab only the plat rate (for now) for each ship
        for item in crestrates.json()['items']:
            for level in item['insurance']:
                if level['level'] == 'Platinum':
                    #shelfrates[item['type']['name']] = {'cost' : level['cost'], 'payout' : level['payout']}
                    shelfrates[item['type']['name']] = level
                    print('added {} with {}'.format(item['type']['name'],level['payout']))

        shelfrates['cache'] = now.replace(seconds=INSURANCE_CACHETIMER)

    if ship in shelfrates.keys():
        return 'Platinum insurance for {} costs {:,.2f} ISK and pays out {:,.2f} ISK'.format(ship, shelfrates[ship]['cost'], shelfrates[ship]['payout'])
    else:
        return 'Ship not found, try again (Case Sensitive)'

if __name__ == '__main__':
    print(insure('Punisher'))
    print(insure('Archon'))
    print(insure('tormentor'))
    print(insure())