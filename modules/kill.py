import arrow
#init
ALLIANCE = 1900696668
# ALLIANCE = 99002172
#ALLIANCE = 1354830081
VALUE = 500000000
BIGVALUE = 20000000000

class Kill():
    def __init__(self, rawkill):
        self.killid = rawkill['package']['killID']
        self.killtime = arrow.get(rawkill['package']['killmail']['killTime'], 'YYYY.MM.DD HH:mm:ss')
        self.attackers = rawkill['package']['killmail']['attackers']
        self.victim = rawkill['package']['killmail']['victim']
        self.value = rawkill['package']['zkb']['totalValue']

    def isBigKill(self):
        return self.value >= BIGVALUE

    def victimAlliance(self):
        try:
            return int(self.victim['alliance']['id']) == ALLIANCE
        except KeyError:
            return False

    def attackerAlliance(self):
        for attacker in self.attackers:
            if 'alliance' in attacker:
                if attacker['alliance']['id'] == ALLIANCE:
                    return True
        return False

    def isOldKill(self):
        return self.killtime < arrow.utcnow().shift(hours=-1)

    def isValuable(self):
        return self.value > VALUE

if __name__ == '__main__':
    import requests
    while True:
        r = requests.get('https://redisq.zkillboard.com/listen.php').json()
        if r:
            try:
                k = Kill(r)
            except TypeError:
                continue
        if k.isOldKill():
            print('Caught an old kill, ignoring', 'age', arrow.utcnow()-k.killtime)
            continue
        if k.victimAlliance():
            if 'alliance' in k.victim:
                print('Victim member of alliance?', k.victimAlliance(), 'checking for', ALLIANCE, 'actual',
                    k.victim['alliance']['id'])
            else:
                print('Victim member of alliance?', k.victimAlliance(), 'checking for', ALLIANCE, 'actual', None)
            continue
        if k.attackerAlliance():
            print('Any attackers in alliance?', k.attackerAlliance())
            continue
        if k.isBigKill():
            print('Big Kill?', k.isBigKill(), 'actual value', k.value)
            continue

