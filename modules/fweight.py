import arrow
import evelink.api
import evelink.corp
import evelink.eve

from config.credentials import FWEIGHT_KEYID, FWEIGHT_VCODE


def fweight(name):
    if name:
        eve = evelink.eve.EVE()
        id = eve.character_id_from_name(name)

        if not id.result:
            return "Character not found"

        contracts, timer = get_contracts()
    
        outstanding, completed, inprogress = get_user_contracts(id.result, contracts)

        return '```Fweight Status for {}\nOutstanding: {}\nInProgress: {}\nCompleted: {}\nNew data {}```'.format(
                name, outstanding, inprogress, completed, arrow.get(timer).humanize())

    else:
        # Get Fweight totals if no name supplied
        contracts, timer = get_contracts()

        outstanding, completed, inprogress = get_total_contracts(contracts)

        return '```Fweight Totals (no name given)\nOutstanding: {}\nInProgress: {}\nCompleted: {}\nNew data {}```'.\
                format(outstanding, inprogress, completed, arrow.get(timer).humanize())


def get_contracts():
    api = evelink.api.API(api_key=(FWEIGHT_KEYID, FWEIGHT_VCODE))
    corp = evelink.corp.Corp(api=api)
    contracts = corp.contracts()
    return contracts.result, contracts.expires


def get_user_contracts(id, contracts):
    outstanding = 0
    completed = 0
    inprogress = 0

    now = arrow.utcnow().replace(month=1)
    for contract in contracts:
        if contracts[contract]['issuer'] == id and now < arrow.get(str(contracts[contract]['issued'])):
            print(arrow.get(contracts[contract]['issued']).humanize())
            if contracts[contract]['status'] == 'Completed':
                completed += 1
            elif contracts[contract]['status'] == 'Outstanding':
                outstanding += 1
            elif contracts[contract]['status'] == 'InProgress':
                inprogress += 1

    return outstanding, completed, inprogress


def get_total_contracts(contracts):
    outstanding = 0
    completed = 0
    inprogress = 0

    for contract in contracts:
        now = arrow.utcnow().replace(month=1)
        if now < arrow.get(contracts[contract]['issued']):
            if contracts[contract]['status'] == 'Completed':
                completed += 1
            elif contracts[contract]['status'] == 'Outstanding':
                outstanding += 1
            elif contracts[contract]['status'] == 'InProgress':
                inprogress += 1

    return outstanding, completed, inprogress

if __name__ == "__main__":
    print(fweight('chainsaw mcginny'))
    print(fweight('imatrain'))
    print(fweight('Nivlac Hita'))
    print(fweight('nopedoesntexist'))
    print(fweight(name=None))
