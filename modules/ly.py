import sqlite3
import operator
from math import sqrt


conn = sqlite3.connect('sqlite-latest.sqlite')
curs = conn.cursor()

def ly(systems_string):
    print(systems_string)
    split = systems_string.split(" ", 1)
    #this is disgusting
    for entry in range(len(split)):
        split[entry] = split[entry] + "%"
    print(split)
    curs.execute('''
        SELECT solarSystemName, x, y, z
        FROM mapSolarSystems
        WHERE solarSystemName LIKE ? or solarSystemName LIKE ?''', split)

    result = curs.fetchmany(6)
    if len(result) < 2:
        return '```Error: one of both systems not found```'
    elif len(result) > 2:
        return '```Error: found too many systems: ' + ', '.join(map(operator.itemgetter(0), result)) + '```'
    
    dist = 0
    for d1, d2 in zip(result[0][1:], result[1][1:]):
        dist += (d1 - d2)**2

    dist = sqrt(dist) / 9.4605284e15 #meters to lightyears (I know)
    ship_ranges = [
            ('CAPITALS:', 3.5), 
            ('SUPER CAP:', 3),
            ('BLOPS:', 4),
            ('JF:', 5)
            ]
    jdc = []
    for ship, jump_range in ship_ranges:
        for level in range(0,6):
            if dist <= jump_range * (1 + level * 0.2):
                jdc.append('%s %d' % (ship, level))
                break
        else:
            jdc.append(ship + ' N/A')

    return '```%s ⟷ %s: %.3f ly\n%s' % (result[0][0], result[1][0], dist, '\n'.join(jdc)) + '```'

    

