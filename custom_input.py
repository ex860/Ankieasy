#!/usr/bin/env python
import sys
import json
import importlib
import os

sys.path.append('anki')
from anki import Collection as aopen

CONFIG_PATH = 'config/customInput.json'

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

def handleCard(data, collection):
    print('deck file:{}'.format(data['deck']))
    print('card_type:{}'.format(data['card_type'] if 'card_type' in data else 'Basic'))

    card_type = data['card_type'] if 'card_type' in data else 'basic'
    card_type = importlib.import_module('cardtype.{}'.format(card_type))
    deck = initAnkiModule(data, collection, card_type)
    for result in data['content']:
        print(result)
        if result is None:
            return
        card_data = card_type.MakeCard(result)

        if 0 == len(card_data):
            return

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

def load_input(path):
    with open(path, encoding='utf-8') as data_file:
        return json.load(data_file)

if '__main__':
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    else:
        input_path = CONFIG_PATH
    data = load_input(input_path)
    collection = data['collection']
    for card in data['cards']:
        handleCard(card, collection)
