import urllib.request
from urllib.parse import quote
from urllib.request import Request, urlopen
import ssl
from bs4 import BeautifulSoup
import subprocess
import platform
import datetime
import json
import re
from hanziconv import HanziConv # https://pypi.python.org/pypi/hanziconv/0.2.1
from re import compile as _Re

_unicode_chr_splitter = _Re( '(?s)((?:[\u2e80-\u9fff])|.)' ).split

def getWord(soup):
    output = ''
    explainWord = soup.find('h1', class_ = 'explain-Word')
    if explainWord != None:
        word = explainWord.find('span', class_ = 'word')
        if word != None:
            output = word.get_text()
    return output

def getSoundAndTitle(soup, download_dir, word):
    output = ''
    phonticLine = soup.find('span', class_ = 'phonitic-line')
    if phonticLine != None:
        sound = phonticLine.find('a', class_ = 'voice-js voice-button')
        dataRel = sound['data-rel']
        soundUrl = 'http://api.frdic.com/api/v2/speech/speakweb?{}'.format(dataRel)
        try:
            urllib.request.urlretrieve(soundUrl, '{}Fr_{}.mp3'.format(download_dir, word))
            output = '[sound:Fr_{}.mp3]'.format(word)
        except urllib.error.HTTPError as err:
            print('FR_err=', err)
    return output

def getContentDict(soup):
    output = []
    caraCnt = -1
    cursorNow = ''
    bs4Comment = BeautifulSoup('<b><!----></b>', "lxml").b.string
    bs4NaviStr = BeautifulSoup('<b>1</b>', "lxml").b.string


    expDiv = soup.find('div', class_ = 'expDiv')
    # modify expDiv
    commonUse = expDiv.find('b', string = '常见用法')
    if commonUse != None:
        element = commonUse
        while element != None:
            if type(element) != type(bs4Comment) and type(element) != type(bs4NaviStr):
                element.clear()
            element = element.next_sibling
    for span in expDiv.find_all('span', recursive = False):
        if span.has_attr('class'):
            if span['class'][0] == 'cara': # Part of speech
                cursorNow = 'cara'
                caraCnt += 1
                contentCnt = 0
                caraDict = dict(cara = span.find_all(text = True, recursive = False), content = [])
                output.append(caraDict)
            if span['class'][0] == 'exp':  # meaning
                if cursorNow == 'exp':
                    print("the <class='exp'> previous <span> can't be <class='exp'>")
                    output[caraCnt]['content'].pop()
                cursorNow = 'exp'
                conDict = dict(exp = span.find_all(text = True, recursive = False), eg = '')
                output[caraCnt]['content'].append(conDict)
            if span['class'][0] == 'eg':   # example sentence
                if cursorNow == 'eg':
                    print("the <class='eg'> previous <span> can't be <class='eg'>")
                    continue
                cursorNow = 'eg'
                output[caraCnt]['content'][contentCnt]['eg'] = span.find_all(text = True, recursive = False)
                contentCnt += 1
    # print(output)
    return output

def contentTruncation(caraList):
    output = caraList
    for cara in output:
        for content in cara['content']:
            if len(content['exp']) > 0:
                content['exp'] = [content['exp'][-1]]
            if len(content['eg']) > 0:
                # content['eg'] = [content['eg'][0]] # customized the number of example sentence
                frenchPart = ''
                chinesePart = ''
                breakIdx = 0
                splitList = _unicode_chr_splitter(content['eg'][0])
                for i in range(0, len(splitList)):
                    if len(splitList[i]) > 0 and ord(splitList[i]) > 10000: 
                        breakIdx = i
                        break
                for i in range(0, len(splitList)):
                    if i < breakIdx:
                        frenchPart += splitList[i]
                    else:
                        chinesePart += splitList[i]
                content['eg'] = dict(FR = frenchPart, CH = chinesePart)
            else:
                content['eg'] = dict(FR = '', CH = '')

    # print(output)
    return output

def makeCard(TrunCaraList, front_word, back_word):
    output = {}
    for cara in TrunCaraList:
        front_word += '({})<br>'.format(cara['cara'][0])
        back_word += '({})<br>'.format(cara['cara'][0])
        for content in cara['content']:
            front_word += '{}<br>'.format(content['eg']['FR'])
            back_word += '{}<br>{}<br>'.format(content['exp'][0], content['eg']['CH'])
    output['front_word'] = front_word
    output['back_word'] = HanziConv.toTraditional(back_word)
    return output

def LookUp(word, download_dir):
    
    result = {}
    front_word = ''
    back_word = ''
    reading = ''
    furi = ''
    furiChild = []
    furiList = []
    text = ''
    textChild = []
    textList = []
    cnt = 0
    sentenceCnt = 1
    differentWord = 1

    opener=urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    ssl._create_default_https_context = ssl._create_unverified_context

    # Eliminate the end of line delimiter
    word = word.splitlines()[0]
    wordUrl = urllib.parse.quote(word, safe='')

    fr_Url = 'http://www.frdic.com/dicts/fr/{}'.format(wordUrl)
    fr_Content = urllib.request.urlopen(fr_Url).read()
    fr_Soup = BeautifulSoup(fr_Content, 'lxml')

    if word == '':
        return None
    # print(fr_Soup)
    word = getWord(fr_Soup)
    print(' ')
    print('<<' + word + '>>')
    print(' ')
    front_word = '{}{}<br>'.format(getSoundAndTitle(fr_Soup, download_dir, word), word)
    caraList = getContentDict(fr_Soup)
    TrunCaraList = contentTruncation(caraList)
    result = makeCard(TrunCaraList, front_word, back_word)
    return result
    