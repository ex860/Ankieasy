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
import math
from hanziconv import HanziConv # https://pypi.python.org/pypi/hanziconv/0.2.1
from re import compile as _Re

_unicode_chr_splitter = _Re( '(?s)((?:[\u2e80-\u9fff])|.)' ).split
verb_type_list = [
    'jisho', 
    'masu', 
    'te', 
    'ta', 
    'nai', 
    'nakatta', 
    'ba', 
    'shieki', 
    'ukemi', 
    'meirei', 
    'kano', 
    'ishi'
]

def getStem(jisho, jishoGana):
    index = -1
    match = False
    if (jisho[index] == jishoGana[index]):
        index = index - 1
        match = True
    else:
        match = False
    while match and -index <= min(len(jisho), len(jishoGana)):
        if (jisho[index] == jishoGana[index]):
            index = index - 1
            match = True
        else:
            match = False
    index = index + 1
    return dict(
        kanji = jisho[0:len(jisho) + index],
        gana = jishoGana[0:len(jishoGana) + index]
    )
    

def getVerb(tr, jisho_masu, typeArray, download_dir):
    obj = {}
    front_word = ''
    read_word = ''
    stem = {}
    kanjiGana = ''

    jisho = jisho_masu.split('・')[0]
    masu = jisho_masu.split('・')[1]

    for typeStr in typeArray:
        typeTd = tr.find('td', class_='katsuyo katsuyo_{}_js'.format(typeStr))
        accentedWord = typeTd.find('span', class_='accented_word')
        if accentedWord != None:
            soundDiv = typeTd.find('div', class_='katsuyo_proc_button clearfix')
            soundStr = soundDiv.find('a', class_='katsuyo_proc_male_button js_proc_male_button')['id']
            # 把數字後兩位數截掉 前面加兩個0 再取後三位
            soundStrNum = ('00{}'.format(str(math.floor(int(soundStr[0:soundStr.find('_')])/100))))[-3:]
            soundUrl = 'http://www.gavo.t.u-tokyo.ac.jp/ojad/sound4/mp3/male/{}/{}.mp3'.format(soundStrNum, soundStr)
            try:
                urllib.request.urlretrieve(soundUrl, '{}{}.mp3'.format(download_dir, soundStr))
                front_word += '[sound:{}.mp3]'.format(soundStr)
            except urllib.error.HTTPError as err:
                print('OJAD_err=', err)
            if typeStr == 'jisho':
                stem = getStem(jisho, accentedWord.get_text())
                kanjiGana = jisho
            elif typeStr == 'masu':
                kanjiGana = masu
            else:
                kanjiGana = accentedWord.get_text().replace(stem['gana'], stem['kanji'], 1)
            front_word += '{}<br>'.format(kanjiGana)
            read_word += '{}[{}]{}<br>'.format(stem['kanji'], stem['gana'], kanjiGana.replace(stem['kanji'], '', 1))
            obj[typeStr] = kanjiGana
    obj['front_word'] = front_word
    obj['read_word'] = read_word
    # print(getStem('書く', 'かく'))
    # print(getStem('伺う', 'うかがう'))
    return obj

def LookUp(word, download_dir):
    
    verbObj = {}
    result = {}
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

    ojad_Url = 'http://www.gavo.t.u-tokyo.ac.jp/ojad/search/index/word:{}'.format(wordUrl)
    ojad_Content = urllib.request.urlopen(ojad_Url).read()
    ojad_Soup = BeautifulSoup(ojad_Content, 'lxml')

    if word == '':
        return None
    
    print(' ')
    print('<< {} >>'.format(word))
    print(' ')

    searchResult = ojad_Soup.find('div', id='search_result')
    table = searchResult.find('table', id='word_table', class_='draggable')
    if table == None:
        print(' ')
        print('<< OJAD word not found !!! >>')
        print(' ')
        return None
    tbody = table.find('tbody')
    tbodyTr = tbody.find('tr') # The default value of tbodyTr is the first row (first <tr>)  
    for tbodyTrIter in tbody.find_all('tr'):
        midashi = tbodyTrIter.find('td', class_='midashi')
        if midashi == None:
            continue
        midashiWrapper = midashi.find('div', class_='midashi_wrapper')
        jisho_masu = midashiWrapper.get_text()
        jisho_masu = jisho_masu.split(chr(10))[1]
        if word == jisho_masu.split('・')[0] or word == jisho_masu.split('・')[1]:
            tbodyTr = tbodyTrIter
            break
    verbObj = getVerb(tbodyTr, jisho_masu, verb_type_list, download_dir)
    print(verbObj)
    result['front_word'] = verbObj['front_word']
    result['back_word'] = ''
    result['read_word'] = verbObj['read_word']
    return result

