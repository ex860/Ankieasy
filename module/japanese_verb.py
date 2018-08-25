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

def getVerb(tr, typeArray, front_word, download_dir):
    result = {}
    back_word = ''
    
    for typeStr in typeArray:
        typeTd = tr.find('td', class_='katsuyo katsuyo_{}_js'.format(typeStr))
        accentedWord = typeTd.find('span', class_='accented_word')
        if accentedWord != None:
            soundDiv = typeTd.find('div', class_='katsuyo_proc_button clearfix')
            soundStr = soundDiv.find('a', class_='katsuyo_proc_female_button js_proc_female_button')['id']
            # 把數字後兩位數截掉 前面加兩個0 再取後三位
            soundStrNum = ('00{}'.format(str(math.floor(int(soundStr[0:soundStr.find('_')])/100))))[-3:]
            soundUrl = 'http://www.gavo.t.u-tokyo.ac.jp/ojad/sound4/mp3/female/{}/{}.mp3'.format(soundStrNum, soundStr)
            try:
                urllib.request.urlretrieve(soundUrl, '{}{}.mp3'.format(download_dir, soundStr))
                front_word += '[sound:{}.mp3]'.format(soundStr)
            except urllib.error.HTTPError as err:
                print('OJAD_err=', err)
            front_word += '{}<br>'.format(accentedWord.get_text())
    result['front_word'] = front_word
    return result

def getJishoMasu(tr, jisho_masu, front_word, download_dir):
    back_word = ''

    jisho_masuCnt = 0
    for typeStr in ['jisho', 'masu']:
        typeTd = tr.find('td', class_='katsuyo katsuyo_{}_js'.format(typeStr))
        soundDiv = typeTd.find('div', class_='katsuyo_proc_button clearfix')
        if soundDiv != None:
            femaleButton = soundDiv.find('a', class_='katsuyo_proc_female_button js_proc_female_button')
            if femaleButton != None:
                soundStr = femaleButton['id']
                # 把數字後兩位數截掉 前面加兩個0 再取後三位
                soundStrNum = ('00{}'.format(str(math.floor(int(soundStr[0:soundStr.find('_')])/100))))[-3:]
                soundUrl = 'http://www.gavo.t.u-tokyo.ac.jp/ojad/sound4/mp3/female/{}/{}.mp3'.format(soundStrNum, soundStr)
                try:
                    urllib.request.urlretrieve(soundUrl, '{}{}.mp3'.format(download_dir, soundStr))
                    front_word += '[sound:{}.mp3]'.format(soundStr)
                except urllib.error.HTTPError as err:
                    print('OJAD_err=', err)
                front_word += '{}<br>'.format(jisho_masu.split('・')[jisho_masuCnt])
                jisho_masuCnt += 1
    return front_word

def getPartOfSpeechBlock(soup, sentenceCnt, front_word, back_word):
    meaning = []
    exampleSentence = {}
    dt = soup.find('dt')
    if dt != None:
        pos = dt.get_text()
        pos = pos.replace(chr(32), '')
        pos = pos.replace(chr(10), '')
        pos = HanziConv.toTraditional(pos)
        front_word += '(' + pos + ')<br>'
        back_word += '(' + pos + ')<br>'
        # print(pos)
    meaning = getMeaning(soup)                             
    exampleSentence = getExampleSentence(soup, sentenceCnt) 
    print('exampleSentence', exampleSentence)
    for i in range(0, len(meaning)):
        front_word += '{}. {}<br>'.format(str(i+1), exampleSentence['JP'][i])
        back_word += '{}. {}<br>{}<br>'.format(str(i+1), meaning[i], exampleSentence['CH'][i])
    return {'front_word': front_word, 'back_word': back_word}

def getMeaning(soup):
    output = []
    for dd in soup.find_all('dd'):
        pContent = dd.find_all('p')
        if pContent[1] != None:
            meaning = pContent[1].get_text()
            meaning = meaning.replace(chr(32), '')
            meaning = meaning.replace(chr(10), '')
            output.append(meaning)
    # print(output)
    return output

def getExampleSentence(soup, sentenceCnt):
    output = {}
    output['JP'] = []
    output['CH'] = []
    sentenceJP = ''
    sentenceCH = ''
    for dd in soup.find_all('dd'):
        ul = dd.find('ul')
        if ul != None:
            cnt = 0
            for li in ul.find_all('li'):
                pJP = li.find('p', class_ = 'def-sentence-from')
                pCH = li.find('p', class_ = 'def-sentence-to')
                if pJP != None:
                    sentenceJP = pJP.get_text()
                    sentenceJP = sentenceJP.replace(chr(32), '')
                    sentenceJP = sentenceJP.replace(chr(10), '')
                if pCH != None:
                    sentenceCH = pCH.get_text()
                    sentenceCH = sentenceCH.replace(chr(32), '')
                    sentenceCH = sentenceCH.replace(chr(10), '')
                output['JP'].append(sentenceJP)
                output['CH'].append(sentenceCH)
                cnt += 1
                if cnt == sentenceCnt:
                    break
        if cnt == 0:
            output['JP'].append('')
            output['CH'].append('')
    # print(output)
    return output


def LookUp(word, download_dir):
    
    result = {}
    front_word = ''
    back_word = ''
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

    hj_Url = 'https://dict.hjenglish.com/jp/jc/{}'.format(wordUrl)
    hj_Content = urllib.request.urlopen(hj_Url).read()
    hj_Soup = BeautifulSoup(hj_Content, 'lxml')

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
    # front_word = getVerb(tbodyTr, ['jisho', 'masu', 'te', 'ta', 'nai', 'nakatta', 'ba', 'shieki', 'ukemi', 'meirei', 'kano', 'ishi'], front_word, download_dir)
    # front_word = getVerb(tbodyTr, ['jisho', 'masu'], front_word, download_dir)
    front_word = getJishoMasu(tbodyTr, jisho_masu, front_word, download_dir)

    wordDetailsContent = hj_Soup.find('section', class_ = 'word-details-content')
    if wordDetailsContent != None:
        for wordDetailsPane in wordDetailsContent.find_all('div', class_ = 'word-details-pane'):
            detailGroups = wordDetailsPane.find('section', class_ = 'detail-groups')
            if detailGroups != None:
                for posSoup in detailGroups.find_all('dl'):
                    frontAndBack = getPartOfSpeechBlock(posSoup, sentenceCnt, front_word, back_word)
                    front_word = frontAndBack['front_word']
                    back_word = frontAndBack['back_word']
            differentWord += 1
            print('front_word', front_word)
            print('back_word', back_word)
        result['front_word'] = front_word
        result['back_word'] = HanziConv.toTraditional(back_word)
        result['read_word'] = ''
        return result
    elif hj_Soup.find('div', class_ = 'word-suggestions') != None:
        print(' ')
        print('<< HJ Word not found!!! >>')
        print(' ')
        return None

