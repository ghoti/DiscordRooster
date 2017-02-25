import arrow
import evelink.api
import evelink.corp
import evelink.eve

from config.credentials import FWEIGHT_KEYID, FWEIGHT_VCODE

def buyback():
    outstanding = parse_contracts(get_contracts())

    return '```Outstanding Buyback Contracts: {}```'.format(outstanding)

def get_contracts():
    api = evelink.api.API(api_key=(FWEIGHT_KEYID, FWEIGHT_VCODE))
    corp = evelink.corp.Corp(api=api)
    contracts = corp.contracts()
    return contracts.result

def parse_contracts(contracts):
    outstanding = 0
    for contract in contracts:
        if contracts[contract]['type'] == 'Item Exchange':
            if contracts[contract]['status'] == 'Outstanding':
                outstanding += 1
    return outstanding

if __name__ == "__main__":
    print(buyback())
