#!/usr/bin/env python
import sys
import json
import importlib
import os
import click
import tkinter as tk

sys.path.append('anki')
from anki import Collection as aopen

INPUT_PATH = 'config/config.json'
INPUT_FOLDER_PATH = 'input'

# @click.command()
# @click.option('-i', '--inputfile', default='input_EY')
# @click.option('-c', '--card_deck', default='英文')
# @click.option('-d', '--dictionary', default='yahoo')
# @click.option('-l', '--language', default='english')
# @click.argument('collection')
# @click.argument('download_dir')
# def info(dictionary, inputfile, card_deck, language, collection, download_dir):
#     profiles = {}
#     profiles['file'] = inputfile
#     profiles['deck'] = card_deck

#     if dictionary.lower() == 'yahoo':
#         profiles['dict_source'] = 'English_Yahoo'
#     elif dictionary.lower() == 'cambridge':
#         profiles['dict_source'] = 'English_Cambridge'
#     elif dictionary.lower() == 'jisho':
#         profiles['dict_source'] = 'japanese_jisho'
#     elif dictionary.lower() == 'mix':
#         profiles['dict_source'] = 'japanese_mix'
#     elif dictionary.lower() == 'verb':
#         profiles['dict_source'] = 'japanese_verb'

#     if language.lower() == 'english' or language.lower() == 'en':
#         profiles['card_type'] = 'basic_reverse'
#     elif language.lower() == 'japanese' or language.lower() == 'jp':
#         profiles['card_type'] = 'japanese_recognition_recall'
    
#     click.echo(collection)
#     click.echo(download_dir)
def initAnkiModule(data, collection, card_type):
    if bool(collection) == False or "deck" not in data:
        print('Collection or deck is not found!')
        return None
    deck = aopen(collection)
    deckId = deck.decks.id(data['deck'])

    deck.decks.select(deckId)
    model = deck.models.byName(card_type.GetCardType(deck.models))
    if model is not None:
        model['did'] = deckId
        deck.models.save(model)
        deck.models.setCurrent(model)
    return deck

def handleProfile(data, collection, download_dir):
    print('words file:{}'.format(data['file']))
    print('deck file:{}'.format(data['deck']))
    print('dict_source :{}'.format(data['dict_source']))
    print('card_type:{}'.format(data['card_type'] if 'card_type' in data else 'Basic'))

    inputFilePath = '{}/{}'.format(INPUT_FOLDER_PATH, data['file'])

    if 'file' not in data or not os.path.exists(inputFilePath):
        print("No input file, Exit")
        return False

    input_file = "{}/{}".format(os.getcwd(), inputFilePath)

    card_type = data['card_type'] if 'card_type' in data else 'basic'

    dict_source = importlib.import_module('module.{}'.format(data['dict_source'].lower()))
    card_type = importlib.import_module('cardtype.{}'.format(card_type))
    deck = initAnkiModule(data, collection, card_type)
    with open(input_file , encoding='utf-8') as word_list:
        for word in word_list:
            result = dict_source.LookUp(word, download_dir)

            if result is None:
                continue
            elif result is False:
                deck.save()
                deck.close()
                return False
            card_data = card_type.MakeCard(result)

            if 0 == len(card_data):
                continue

            card = deck.newNote()
            for key in card_data:
                card[key] = card_data[key]
            try:
                deck.addNote(card)
            except(Exception, e):
                if hasattr(e, "data"):
                    sys.exit("ERROR: Cound not add {}:{}", e.data["field"], e.data['type'])
                else:
                    sys.exit(e)
    deck.save()
    deck.close()

def load_config(path):
    with open(path, encoding='utf-8') as data_file:
        return json.load(data_file)

def main():
    if len(sys.argv) >= 2:
        config_path = sys.argv[1]
    else:
        config_path = INPUT_PATH
    data = load_config(config_path)
    collection = data['collection']
    download_dir = data['download_dir']
    for profile in data['profiles']:
        if handleProfile(profile, collection, download_dir) == False:
            break
    # info()

if '__main__':
    # win = tk.Tk()
    # win.title("Ankieasy")
    # label = tk.Label(win, text="Hello~")
    # label.pack()
    # button = tk.Button(win, text="確定", command=main).pack()
    # win.mainloop()
    main()