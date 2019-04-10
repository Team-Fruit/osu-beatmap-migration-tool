import sys
import json
import re
from multiprocessing import Pool
from functools import partial
from requests import session


def download(id, session):
    req = session.get('https://osu.ppy.sh/d/' + id, stream=True)
    
    if 'Content-Disposition' not in req.headers:
        print('Beatmap %s could not be found will be skipped' % id)
        return

    osz = req.headers['Content-Disposition'][21:-2]
    print(osz)
    osz = re.sub(r'(?:["*:<>?\\]|\/|\|)', ' ', osz)
    with open(osz, 'wb') as o:
        for chunk in req.iter_content(chunk_size=64 * 1024):
            if chunk:
                o.write(chunk)
                o.flush()

def main():
    args = sys.argv
    if len(args) != 3:
        print('osu account id, password is required')
        return
    with session() as s:
        para = {
            'action': 'login',
            'username': args[1],
            'password': args[2],
            'redirect': 'index.php',
            'sid': '',
            'login': 'Login'
        }
        r = s.post('http://osu.ppy.sh/forum/ucp.php', data=para)
        with open('beatmaps.json', 'r') as f:
            ids = json.load(f)
        with Pool(4) as p:
            p.map(partial(download, session=s), ids)       

if __name__ == '__main__':
    main()
