from os import path, listdir
import json


def main():
    dir = path.dirname(path.abspath(__file__))
    songs = set()
    for song in listdir(dir):
        id = song.split(' ')[0]
        if id.isdigit():
            songs.add(id)
    with open('beatmaps.json', 'w') as f:
        json.dump(list(songs), f, ensure_ascii=False)

if __name__ == '__main__':
    main()
