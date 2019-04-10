import glob
import json


def main():
    songs = [id for id in map(lambda p: p.split(' ')[0], glob.iglob('*/')) if id.isdigit()]

    with open('beatmaps.json', 'w') as f:
        json.dump(songs, f, ensure_ascii=False)

if __name__ == '__main__':
    main()
