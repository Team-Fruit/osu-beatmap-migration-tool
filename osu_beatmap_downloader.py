import argparse
import sys
import json
import re
import glob
from multiprocessing import Pool
from functools import partial
from requests import session


parser = argparse.ArgumentParser(description='osu! beatmap downloader')

parser.add_argument('username', help='osu! account username')
parser.add_argument('password', help='osu! account password')
parser.add_argument('-s', '--skip', help='Skip if beatmap file already exists', action='store_true')

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
    args = parser.parse_args()

    with open('beatmaps.json', 'r') as f:
        ids = json.load(f)

    if args.skip:
        for id in map(lambda path: path.split(' ')[0], glob.glob('*.osz')):
            ids.remove(id)

    with session() as s:
        para = {
            'action': 'login',
            'username': args.username,
            'password': args.password,
            'redirect': 'index.php',
            'sid': '',
            'login': 'Login'
        }
        r = s.post('http://osu.ppy.sh/forum/ucp.php', data=para)
        with Pool(4) as p:
            p.map(partial(download, session=s), ids)       

if __name__ == '__main__':
    main()
