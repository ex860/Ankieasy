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
    
    f = open('output.txt', 'w', encoding='utf8')
    data = load_input(CONFIG_PATH)
    collection = data['collection']

    deck = aopen(collection)
    deckId = deck.decks.id('日文')
    deck.decks.select(deckId)

    cnt = 0
    for note in deck.findNotes('male.mp3'):
        Note = deck.getNote(note)
        expression = Note.__getitem__('Expression')

        # Find the Jisho form for LookUp
        firstMp3 = expression.find('male.mp3')
        firstLessSign = expression[firstMp3:].find('<')
        jisho = expression[firstMp3 + 9:firstMp3 + firstLessSign]
        # print(jisho)
        if (jisho == '' or jisho == '預かる' or jisho == '舐める'):
            continue

        res = OJAD.LookUp(jisho, download_dir)
        # print(res['front_word'])
        lastMp3 = expression.rfind('male.mp3')
        firstGreaterSign = expression[lastMp3:].find('>')
        # print(res['front_word'] + expression[lastMp3 + firstGreaterSign + 1:])
        Note.__setitem__('Expression', res['front_word'] + expression[lastMp3 + firstGreaterSign + 1:])
        Note.flush()
        # f.write(jisho + '\n' + expression[0:lastMp3 + firstGreaterSign + 1] + '\n')
        cnt = cnt + 1
        if (cnt == 3):
            break
    deck.save()
    deck.close()