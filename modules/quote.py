import json

ARCHIVING_FILE = "./quote_archive.json"
CACHE = {}


def load_archives():
    global CACHE
    with open(ARCHIVING_FILE, 'r') as f:
        try:
            CACHE = json.load(f)
        except FileNotFoundError:
            return


def write_archives():
    with open(ARCHIVING_FILE, 'w') as f:
        json.dump(CACHE, f)


def get_quote(key):
    try:
        if not CACHE:
            load_archives()
        return CACHE[key]
    except KeyError:
        return "No quote for that key found :("


def store_quote(key, value):
    CACHE[key] = value
    write_archives()
