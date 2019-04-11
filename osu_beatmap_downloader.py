import json
import re
import glob
import shutil
import os
from argparse import ArgumentParser
from multiprocessing import Pool, freeze_support, RLock, Manager
from functools import partial
from requests import session
from tqdm import tqdm


def pbar_desc_size():
    return str(int(shutil.get_terminal_size().columns/4))

def download(session, pids, id):
    req = session.get('https://osu.ppy.sh/d/' + id, stream=True)
    
    if 'Content-Disposition' not in req.headers:
        return 'Beatmap {} could not be found will be skipped'.format(id)

    osz = req.headers['Content-Disposition'][21:-2]
    osz = re.sub(r'(?:["*:<>?\\]|\/|\|)', ' ', osz)
    desc = osz[osz.find(' ')+1:-4]
    size = int(req.headers['Content-Length'])

    pid = os.getpid()
    if pid not in pids:
        pids.append(pid)
    position = pids.index(pid)+1

    desc_size = pbar_desc_size()
    progress = tqdm(
            total=size,
            unit='B',
            unit_scale=True,
            position=position,
            desc=desc,
            ascii=True,
            bar_format='{desc:'+desc_size+'.'+desc_size+'}{percentage:3.0f}%|{bar}{r_bar}')
    with open(osz, 'wb') as o:
        for chunk in req.iter_content(chunk_size=64 * 1024):
            if chunk:
                o.write(chunk)
                o.flush()
                progress.update(len(chunk))
        progress.close()

def main():
    parser = ArgumentParser(description='osu! beatmap downloader')

    parser.add_argument('username', help='osu! account username')
    parser.add_argument('password', help='osu! account password')
    parser.add_argument('-s', '--skip', help='Skip if beatmap file already exists', action='store_true')

    args = parser.parse_args()

    with open('beatmaps.json', 'r') as f:
        ids = json.load(f)

    if args.skip:
        for id in map(lambda path: path.split(' ')[0], glob.iglob('*.osz')):
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
        res = s.post('https://osu.ppy.sh/forum/ucp.php', data=para)

        freeze_support()
        with Pool(4, initializer=tqdm.set_lock, initargs=(RLock(),)) as p:
            with Manager() as manager:
                desc_size = pbar_desc_size()
                for c in tqdm(
                        p.imap_unordered(partial(download, s, manager.list()), ids),
                        total=len(ids),
                        bar_format='{desc:'+desc_size+'.'+desc_size+'}{percentage:3.0f}%|{bar}{r_bar}',
                        desc='Overall',
                        position=0):
                    if c:
                        tqdm.write(c)
                    pass    

if __name__ == '__main__':
    main()
