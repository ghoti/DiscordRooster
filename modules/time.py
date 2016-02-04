import arrow

def time():
    utc = arrow.utcnow()
    time = utc.format('YYYY-MM-DD HH:mm:ss ZZ')
    return time

if __name__ == '__main__':
    print(time())
