import pycrest
import shelve

def price(item=None):
    if not item:
        return 'Need something to price, dum dum'

    if item.lower() == 'plex':
        return 'plex'



if __name__ == '__main__':
    print(price())
    print(price('plex'))
    print(price('stabber'))
    print(price('stabber fleet'))