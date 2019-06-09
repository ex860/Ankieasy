#!/usr/bin/env python
import sys
import json
import importlib
import os
import re
import constant
import tkinter as tk
from pprint import pprint

sys.path.append('anki')
from anki import Collection as aopen

START = 'start'
END_OF_DICT = '----'

def initAnkiModule(data, collection, cardType):
    if bool(collection) == False:
        print('Collection is not found!')
        return None
    elif 'name' not in data:
        print('deck is not found!')
        return None
    deck = aopen(collection)
    deckId = deck.decks.id(data['name'])

    deck.decks.select(deckId)
    model = deck.models.byName(cardType.GetCardType(deck.models))
    
    if model is not None:
        model['did'] = deckId
        deck.models.save(model)
        deck.models.setCurrent(model)
    return deck

def getExplanation(deckInfo, collection, download_dir):
    for deckInfoData in deckInfo:
        if 'inputWord' in deckInfoData:
            print('deckInfoData', deckInfoData)
            print('deck_file: {}'.format(deckInfoData['name']))
            print('dict_source: {}'.format(deckInfoData['webDict']))
            print('card_type: {}'.format(deckInfoData['cardType'] if 'cardType' in deckInfoData else 'Basic'))
            
            cardType = deckInfoData['cardType'] if 'cardType' in deckInfoData else 'basic'
            webDict = importlib.import_module('module.{}'.format(deckInfoData['webDict'].lower()))

            for cardTypeIter in constant.cardTypeMap:
                if deckInfoData['cardType'] in cardTypeIter['string']:
                    mapping = cardTypeIter['name']
                    cardType = importlib.import_module('cardtype.{}'.format(mapping))
                    break

            deck = initAnkiModule(deckInfoData, collection, cardType)
            for word in deckInfoData['inputWord']:
                if len(word) >= 1:
                    word = word.splitlines()[0]
                    result = webDict.LookUp(word, download_dir)
                    if result is None:
                        continue
                    elif result is False:
                        deck.save()
                        deck.close()
                        return False
                    cardData = cardType.MakeCard(result)

                    if 0 == len(cardData):
                        continue

                    card = deck.newNote()
                    for key in cardData:
                        card[key] = cardData[key]
                    try:
                        deck.addNote(card)
                    except(Exception, e):
                        if hasattr(e, 'data'):
                            sys.exit('ERROR: Cound not add {}:{}', e.data['field'], e.data['type'])
                        else:
                            sys.exit(e)
            deck.save()
            deck.close()
    return

def load_config(path):
    with open(path, encoding = 'utf-8') as data_file:
        return json.load(data_file)

def getDeckInfo(collection, enableDefault):
    deck = aopen(collection)
    deckInfo = []
    for ankiDeck in deck.decks.all():
        # print(ankiDeck['name'])                         # Name of the deck
        # print(deck.models.get(ankiDeck['mid'])['name']) # Card type of the deck
        if enableDefault == False:
            if ankiDeck['name'] == '預設' or ankiDeck['name'] == 'Default':
                continue
        deckInfo.append(dict(name = ankiDeck['name'], cardType = deck.models.get(ankiDeck['mid'])['name']))
    # print(deckInfo)
    deck.save()
    deck.close()
    return deckInfo

def getWebDictAndInputWord(inputData, deckInfo):
    for deck in deckInfo:
        for webDict in constant.webDict:
            if deck['name'] == webDict['name']:
                deck.update(webDict)
                break
    for deck in deckInfo:
        for data in inputData:
            if deck['name'] == data['name']:
                deck.update(data)
                break
    return deckInfo


if '__main__':
    master = tk.Tk()
    master.title('Ankieasy')
    master.geometry('700x300')
    tk.Label(master, text = '請輸入collection以及下載的路徑')
    tk.Label(master, text = 'collection路徑:').grid(row = 0)
    tk.Label(master, text = '日文').grid(row = 1)
    tk.Label(master, text = '英文').grid(row = 2)
    tk.Label(master, text = '英文句子').grid(row = 3)

    collectStr = tk.StringVar()

    collection = tk.Entry(master, width = 70, textvariable = collectStr)
    JPText = tk.Text(master, width = 70, height = 5)
    ENText = tk.Text(master, width = 70, height = 5)
    ENSentText = tk.Text(master, width = 70, height = 5)

    collection.insert(0, 'C:/Users/Yu-Hsien/AppData/Roaming/Anki2/YuHsien/collection.anki2')

    collection.grid(row = 0, column = 1)
    JPText.grid(row = 1, column = 1)
    ENText.grid(row = 2, column = 1)
    ENSentText.grid(row = 3, column = 1)

    def mainProcess():
        enableDefault = False
        deckInfo = getDeckInfo(collectStr.get(), enableDefault)
        inputWord = [
            {
                'name':'日文',
                'inputWord':JPText.get('1.0', 'end').split('\n')
            },
            {
                'name':'英文',
                'inputWord':ENText.get('1.0', 'end').split('\n')
            },
            {
                'name':'英文片語',
                'inputWord':ENSentText.get('1.0', 'end').split('\n')
            }
        ]
        deckInfo = getWebDictAndInputWord(inputWord, deckInfo)
        pprint(deckInfo)
        downloadStr = re.sub('anki2$', 'media/', collectStr.get())
        getExplanation(deckInfo, collectStr.get(), downloadStr)
        master.destroy()

    button = tk.Button(master, text = '開始擷取', command = mainProcess)
    button.grid(row = 4, column = 1)

    master.mainloop()