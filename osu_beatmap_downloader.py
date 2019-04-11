import json
import aiohttp
import asyncio
import re
import shutil
from argparse import ArgumentParser
from tqdm import tqdm


class PositionManager:

    def __init__(self, size):
        self.size = size
        self.dict = {}

    def get_position(self, id):
        if id in self.dict:
            return self.dict[id]

        positions = self.dict.values()
        position = next(filter(lambda x: x not in positions, range(1, self.size+1)))
        self.dict[id] = position
        return position

    def done(self, id):
        del self.dict[id]

def pbar_desc_size():
    return str(int(shutil.get_terminal_size().columns/4))

async def download(session, position_manager, url):
    async with session.get(url) as res:
        if "Content-Disposition" not in res.headers:
            tqdm.write("Beatmap {} could not be found will be skipped".format(id))

        osz = res.headers["Content-Disposition"][21:-2]
        osz = re.sub(r'(?:["*:<>?\\]|\/|\|)', ' ', osz)
        desc = osz[osz.find(' ')+1:-4]
        size = int(res.headers['Content-Length'])

        desc_size = pbar_desc_size()
        progress = tqdm(
                total=size,
                unit='B',
                unit_scale=True,
                desc=desc,
                ascii=True,
                position=position_manager.get_position(url),
                bar_format='{desc:'+desc_size+'.'+desc_size+'}{percentage:3.0f}%|{bar}{r_bar}')
        
        with open(osz, "wb") as o:
            while True:
                chunk = await res.content.read(4 * 1024)
                if not chunk:
                    break
                o.write(chunk)
                progress.update(len(chunk))
            progress.close()
            position_manager.done(url)

async def parallel_download(username, password, ids, limit=4):
    async with aiohttp.ClientSession() as session:
        data = {
            "action": "login",
            "username": username,
            "password": password,
            "redirect": "index.php",
            "sid": "",
            "login": "Login"
        }
        async with session.post("https://osu.ppy.sh/forum/ucp.php", data=data) as res:
            sem = asyncio.Semaphore(limit)

            async def limited_download(session, position_manager, url):
                with await sem:
                    return await download(session, position_manager, url)

            position_manager = PositionManager(limit)
            tasks = [limited_download(session, position_manager, "https://osu.ppy.sh/d/" + id) for id in ids]

            desc_size = pbar_desc_size()
            for f in tqdm(asyncio.as_completed(tasks),
                    total=len(ids),
                    bar_format='{desc:'+desc_size+'.'+desc_size+'}{percentage:3.0f}%|{bar}{r_bar}',
                    desc='Overall',
                    position=0):
                await f

def main():
    parser = ArgumentParser(description="osu! beatmap downloader")

    parser.add_argument("username", help="osu! account username")
    parser.add_argument("password", help="osu! account password")
    parser.add_argument("-s", "--skip", help="Skip if beatmap file already exists", action="store_true")

    args = parser.parse_args()

    with open("beatmaps.json", "r") as f:
        ids = json.load(f)

    if args.skip:
        for id in map(lambda path: path.split(" ")[0], glob.iglob("*.osz")):
            ids.remove(id)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(parallel_download(args.username, args.password, ids))

if __name__ == "__main__":
    main()