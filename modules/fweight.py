import arrow
import evelink.api
import evelink.corp
import evelink.eve

from config.credentials import FWEIGHT_KEYID, FWEIGHT_VCODE

def fweight(name):

    if not name:
        return 'NEED A NAME WTF'

    eve = evelink.eve.EVE()
    id = eve.character_id_from_name(name)

    if not id.result:
        return "Character not found"

    contracts, timer = get_contracts()
    
    completed, outstanding, inprogress = get_user_contracts(id.result, contracts)

    return '```Fweight Statuss for {}\nOutstanding: {}\nInProgress: {}\nCompleted: {}\nNew data in {}```'.format(
            name, outstanding, inprogress, completed, arrow.get(timer).humanize())


def get_contracts():
    api = evelink.api.API(api_key=(FWEIGHT_KEYID, FWEIGHT_VCODE))
    corp = evelink.corp.Corp(api=api)
    contracts = corp.contracts()
    return contracts.result, contracts.expires


def get_user_contracts(id, contracts):
    outstanding = 0
    completed = 0
    inprogress = 0

    for contract in contracts:
        print(contracts[contract]['status'])
        if contracts[contract]['issuer'] == id:
            if contracts[contract]['status'] == 'Completed':
                completed += 1
            elif contracts[contract]['status'] == 'Outstanding':
                outstanding += 1
            elif contracts[contract]['status'] == 'InProgress':
                inprogress += 1

    return outstanding, completed, inprogress

if __name__ == "__main__":
    print(fweight('chainsaw mcginny'))
    print(fweight('Nivlac Hita'))
    print(fweight('nopedoesntexist'))