import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup
import ssl
import subprocess
import platform
import datetime
import json
import re
from re import compile as _Re

_unicode_chr_splitter = _Re( '(?s)((?:[\u2e80-\u9fff])|.)' ).split

def getRealWord(soup, front_word):
    word = soup.find('div', class_ = 'compTitle mt-25 ml-25 mb-10').h3.get_text()
    front_word += '{}<br>'.format(word)
    return front_word

def getCBSound(soup, front_word, word, download_dir):
    tabEntry = soup.find('div', class_ = 'entrybox')
    if tabEntry is None:
        print("<< CBSound Not Found !!! (entrybox not found) >>")
        return front_word

    partOfSpeech = tabEntry.find_all('div', class_='entry-body__el clrd js-share-holder')
    if len(partOfSpeech) == 0:
        print("<< CBSound Not Found !!! (entry-body__el clrd js-share-holder not found)>>")
        return front_word
    sound = partOfSpeech[0].find('span', attrs={'data-src-mp3':True})

    if sound is not None and bool(download_dir) != False:
        try:
            urllib.request.urlretrieve('https://dictionary.cambridge.org{}'.format(sound['data-src-mp3']), '{}Py_{}.mp3'.format(download_dir, word))
            front_word = '[sound:Py_{}.mp3]'.format(word) + front_word
        except urllib.error.HTTPError as err:
            print("HTTP Error:", err)

    return front_word

def getSound(soup, front_word, word, download_dir):
    dictionaryWordCard = soup.find('div', class_ = 'dictionaryWordCard')
    print(dictionaryWordCard)
    soundSpan = dictionaryWordCard.find('span', class_ = 'dict-sound')
    if soundSpan != None:
        soundAudio = soundSpan.find('audio')
        print('soundAudio', soundAudio)
        # try:
        #     urllib.request.urlretrieve('', '{}Eng_{}.mp3'.format(download_dir, word))
        #     front_word += '[sound:Eng_{}.mp3]<br>'.format(word)
        # except urllib.error.HTTPError as err:
        #     print('Eng_err=', err)
    return front_word

def getMeaning(soup):
    posDict = dict(meaningArray = [])
    cardDict = []
    explainTab = soup.find('div', class_='grp grp-tab-content-explanation tabsContent tab-content-explanation tabActived')
    if explainTab != None:
        ul = explainTab.ul
        for li in ul.find_all('li'):
            divIsPOS = li.find('div', class_=' tabs-pos_type fz-14')
            spanIsMeaning = li.find('span', class_=' fz-14')
            if divIsPOS != None:
                if not isinstance(posDict, str): # Check whether the type of posDict is str or not
                    cardDict.append(posDict)
                posString = '({})'.format(divIsPOS.get_text())
                posDict = dict(pos = posString, meaningArray = [])
            elif spanIsMeaning != None:
                exampleSentence = ''
                if li.p != None:
                    exampleSentence = li.p.span.get_text()
                splitList = _unicode_chr_splitter(exampleSentence)    
                englishPart = ''
                chinesePart = ''
                breakIdx = 0
                for i in range(0, len(splitList)):
                    if len(splitList[i]) > 0 and ord(splitList[i]) > 10000: 
                        breakIdx = i
                        break
                for i in range(0, len(splitList)):
                    if i < breakIdx:
                        englishPart += splitList[i]
                    else:
                        chinesePart += splitList[i]
                meaningDict = dict(meaning = spanIsMeaning.get_text(), english = englishPart, chinese = chinesePart)
                posDict['meaningArray'].append(meaningDict)
        cardDict.append(posDict)
    else:
        dictionaryWordCard = soup.find('div', class_ = 'dd cardDesign dictionaryWordCard sys_dict_word_card')
        compList = dictionaryWordCard.find('div', class_ = 'compList mb-25 ml-25 p-rel')
        if compList == None:
            return None
        else:
            for li in compList.ul.find_all('li'):
                pos = ''
                posDiv = li.find('div', class_ = ' pos_button fz-14 fl-l mr-12')
                if posDiv != None:
                    pos = posDiv.get_text()
                meaning = ''
                meaningDiv = li.find('div', class_ = ' fz-16 fl-l dictionaryExplanation')
                if meaningDiv != None:
                    meaning = meaningDiv.get_text()
                posDict = dict(pos = '({})'.format(pos), meaningArray = [])
                meaningDict = dict(meaning = meaning, english = '', chinese = '')
                posDict['meaningArray'].append(meaningDict)
                cardDict.append(posDict)
    return cardDict

def fillInResult(cardDict, front_word, back_word):
    result = {}
    for pos in cardDict:
        if 'pos' in pos: # Check whether there is a key called 'pos' in this dict
            front_word += '{}<br>'.format(pos['pos'])
            back_word += '{}<br>'.format(pos['pos'])
        cnt = 1
        for meaning in pos['meaningArray']:
            front_word += '{}. {}<br>'.format(str(cnt), meaning['english'])
            back_word  += '{}<br>{}<br>'.format(meaning['meaning'], meaning['chinese'])
            cnt += 1
    result['front_word'] = front_word
    result['back_word'] = back_word
    return result

def LookUp(word, download_dir):
    # Eliminate the end of line delimiter
    word = word.splitlines()[0]
    wordUrl = urllib.parse.quote(word, safe='')
    url='https://tw.dictionary.search.yahoo.com/search?p={}'.format(wordUrl)
    
    opener=urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    ssl._create_default_https_context = ssl._create_unverified_context
    
    content = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(content, 'lxml')

    wordUrl = wordUrl.replace('%20','-')
    wordUrl = wordUrl.replace('%27','-')
    wordUrl = wordUrl.replace('%28','-')
    wordUrl = wordUrl.replace('%29','-')
    wordUrl = wordUrl.replace('%2F','-')
    wordUrl = wordUrl.replace('--','-')

    url='https://dictionary.cambridge.org/us/dictionary/english/{}'.format(wordUrl)
    content = urllib.request.urlopen(url).read()
    CBSoup = BeautifulSoup(content, 'lxml')

    result = {}
    front_word = ''
    back_word = ''

    if word == '':
        return None

    print(' ')
    print('<<' + word + '>>')
    print(' ')

    notFound = soup.find('div', class_ = 'dd cardDesign pt-25 pb-25 pl-120 pr-120 sys_dict_zrp')
    if notFound != None:
        print(' ')
        print('<< word not found!!! >>')
        print(' ')
        return None

    front_word = getRealWord(soup, front_word)
    front_word = getCBSound(CBSoup, front_word, word, download_dir)
    # front_word = getSound(soup, front_word, word, download_dir)
    cardDict = getMeaning(soup)
    if cardDict == None:
        print(' ')
        print('<< meaning not found!!! >>')
        print(' ')
        return None
    result = fillInResult(cardDict, front_word, back_word)
    
    print(result)
    return result
