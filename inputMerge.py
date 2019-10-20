#!/usr/bin/env python
import sys
import json
import importlib
import os
import click

sys.path.append('anki')
from anki import Collection as aopen

CONFIG_PATH = 'config/inputMergeConfig.json'
INPUT_FOLDER_PATH = 'input'
START = 'start'
END_OF_DICT = '----'

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

def handleProfile(data, collection, download_dir, inputFilePath):
    print('deck file:{}'.format(data['deck']))
    print('dict_source :{}'.format(data['dict_source']))
    print('card_type:{}'.format(data['card_type'] if 'card_type' in data else 'Basic'))
    
    if not os.path.exists("{}/{}".format(INPUT_FOLDER_PATH, inputFilePath)):
        print("No input file, Exit")
        return False

    input_file = "{}/{}/{}".format(os.getcwd(), INPUT_FOLDER_PATH, inputFilePath)

    card_type = data['card_type'] if 'card_type' in data else 'basic'

    dict_source = importlib.import_module('module.{}'.format(data['dict_source'].lower()))
    dict_source_str = '[{}]'.format(data['dict_source'].lower())
    card_type = importlib.import_module('cardtype.{}'.format(card_type))
    deck = initAnkiModule(data, collection, card_type)
    stat = None
    with open(input_file , encoding='utf-8') as word_list:
        for word in word_list:
            word = word.splitlines()[0]
            if stat == START and word != END_OF_DICT:
                result = dict_source.LookUp(word, download_dir)

                if result is None:
                    continue
                elif result is False:
                    deck.save()
                    deck.close()
                    return False

                # Mapping keys from result object to Anki's template (card_data):
                # front_word -> Expression
                # back_word  -> Meaning
                # read_word  -> Reading
                card_data = card_type.MakeCard(result)

                if 0 == len(card_data):
                    continue

                note = deck.newNote()
                for key in card_data:
                    note[key] = card_data[key]
                try:
                    deck.addNote(note)
                except(Exception, e):
                    if hasattr(e, "data"):
                        sys.exit("ERROR: Cound not add {}:{}", e.data["field"], e.data['type'])
                    else:
                        sys.exit(e)
            elif stat == START and word == END_OF_DICT:
                stat = None
            elif stat == None:
                if word == dict_source_str:
                    stat = START
    deck.save()
    deck.close()

def load_config(path):
    with open(path, encoding='utf-8') as data_file:
        return json.load(data_file)

if '__main__':
    if len(sys.argv) >= 2:
        config_path = sys.argv[1]
    else:
        config_path = CONFIG_PATH
    data = load_config(config_path)
    inputFilePath = data['input']
    collection = data['collection']
    download_dir = data['download_dir']
    for profile in data['profiles']:
        if handleProfile(profile, collection, download_dir, inputFilePath) == False:
            break