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


def get_key_list():
    resp = "Existing keys: \n"
    for key, _ in CACHE:
        resp += key + ", "

    return resp


def delete_quote(key):
    if key in CACHE:
        del CACHE[key]
        return "Killed any witnesses of the deletion of {}".format(key)
    else:
        return "Something's not quite right."


def store_quote(key, value):
    CACHE[key] = value
    write_archives()
