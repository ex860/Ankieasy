import sys
import json
import importlib
import os
import module.japanese_verb as OJAD

sys.path.append('anki')
from anki import Collection as aopen
from anki.tags import TagManager

CONFIG_PATH = 'config/customInput.json'
download_dir = 'C:/Users/Yu-Hsien/AppData/Roaming/Anki2/YuHsien/collection.media/'

def load_input(path):
    with open(path, encoding='utf-8') as data_file:
        return json.load(data_file)

if '__main__':
    data = load_input(CONFIG_PATH)
    collection = data['collection']
    deck = aopen(collection)
    # print(deck.tags.allItems())
    # print(deck.tags.all())
    print('------------------------------')
    # print(deck.getNote(deck.findNotes('male.mp3')[5]).items())
    # print(deck.getNote(deck.findNotes('male.mp3')[55]).__getitem__('Expression'))
    # print('>>>>>>>>>>>>>>')
    # print(deck.getNote(deck.findNotes('male.mp3')[55]).__getitem__('Reading'))
    res = OJAD.LookUp('打ち合う', download_dir)
    # print(res)