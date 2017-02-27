import arrow
import evelink.api
import evelink.corp
import evelink.eve

from config.credentials import FWEIGHT_KEYID, FWEIGHT_VCODE

def buyback():
    outstanding, value = parse_contracts(get_contracts())

    return '```Outstanding Buyback Contracts: {}\nTotal value: {:,}```'.format(outstanding, value)

def get_contracts():
    api = evelink.api.API(api_key=(FWEIGHT_KEYID, FWEIGHT_VCODE))
    corp = evelink.corp.Corp(api=api)
    contracts = corp.contracts()
    return contracts.result

def parse_contracts(contracts):
    outstanding = 0
    value = 0
    for contract in contracts:
        if contracts[contract]['type'] == 'ItemExchange':
            if contracts[contract]['status'] == 'Outstanding':
                if contracts[contract]['issuer'] != 95548667:
                    outstanding += 1
                    value += contracts[contract]['price']
    return outstanding, value

if __name__ == "__main__":
    print(buyback())
