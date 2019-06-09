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
import base64
from hanziconv import HanziConv # https://pypi.python.org/pypi/hanziconv/0.2.1
from re import compile as _Re

_unicode_chr_splitter = _Re( '(?s)((?:[\u2e80-\u9fff])|.)' ).split

def getWord(soup):
    output = ''
    wordText = soup.find('div', class_='word-text')
    h2 = wordText.find('h2')
    if h2 != None:
        output = h2.get_text()
    return output

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
    meaning = getMeaning(soup)
    exampleSentence = getExampleSentence(soup, sentenceCnt)
    # print(exampleSentence)
    for i in range(0, len(meaning)):
        front_word += str(i+1) + '. ' + exampleSentence['JP'][i] + '<br>'
        back_word += str(i+1) + '. ' + meaning[i] + '<br>' + exampleSentence['CH'][i] + '<br>'
    return {'front_word': front_word, 'back_word': back_word}

def getSoundUrl(playStr):
    url = ''
    removeReturn = playStr.split(';')[0]
    removeRightParenthesis = removeReturn.split(')')[0]
    removeLeftParenthesis = removeRightParenthesis.split('(')[1]
    paramGroup = removeLeftParenthesis.split(',')
    newParamGroup = []
    for param in paramGroup:
        if param[0] == "'" and param[-1] == "'": # If the string is embraced by single quote,
            param = param[1:-1]                  # Remove the single quotes
        newParamGroup.append(param)
    if newParamGroup[4] != '':
        url = 'https://audio00.forvo.com/audios/mp3/{}'.format(base64.b64decode(newParamGroup[4]).decode('ascii'))
    elif newParamGroup[1] != '':
        url = 'https://audio00.forvo.com/mp3/{}'.format(base64.b64decode(newParamGroup[1]).decode('ascii'))
    return url

def getForvoSound(soup, download_dir, word):
    section = soup.find('section', class_='main_section')
    articleJP = ''
    articleList = section.find_all('article', class_='pronunciations')
    for article in articleList:
        if article.find('header') != None:
            if article.find('header').find('em') != None:
                if article.find('header').find('em').get('id') != None:
                    if article.find('header').find('em')['id'] == 'ja':
                        articleJP = article
                        break
    if articleJP == '':
        print(' ')
        print('<< Forvo Japanese pronunciation not found!!! >>')
        print(' ')
        return ''
        
    ul = articleJP.find('ul')
    liGroup = ul.find_all('li')
    authorList = []
    soundUrlList = []
    for li in liGroup:
        author = ''
        soundUrl = ''
        spanPlay = li.find('span', class_='play')
        spanOfLink = li.find('span', class_='ofLink')
        if spanPlay != None and spanOfLink != None:
            spanOnClick = spanPlay['onclick']
            soundUrl = getSoundUrl(spanOnClick)
            if spanOfLink.get('data-p2'):
                author = spanOfLink['data-p2']
            else:
                author = ''
            authorList.append(author)
            soundUrlList.append(soundUrl)
    finalAuthor = ''
    finalSoundUrl = ''
    getAuthorInRecommendedList = False
    if 'strawberrybrown' in authorList:
        finalAuthor = 'strawberrybrown'
        finalSoundUrl = soundUrlList[authorList.index('strawberrybrown')]
    else:
        for author in authorList:
            if author in ['akitomo', 'kaoring', 'kyokotokyojapan', 'kiiro', 'yasuo', 'sorechaude', 'Phlebia']:
                finalAuthor = author
                finalSoundUrl = soundUrlList[authorList.index(author)]
                getAuthorInRecommendedList = True
                break
        if getAuthorInRecommendedList == False:
            finalAuthor = authorList[0]
            finalSoundUrl = soundUrlList[0]
    try:
        urllib.request.urlretrieve(finalSoundUrl, download_dir + 'Jp_' + word + '.mp3')
        output = '[sound:Jp_' + word + '.mp3]'
    except urllib.error.HTTPError as err:
        print('Forvo_err=', err)
    return output

def getMeaning(soup):           # list
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

def getExampleSentence(soup, sentenceCnt):   # dict
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
    needHJSound = True
    sentenceCnt = 1
    differentWord = 1

    opener=urllib.request.build_opener()
    opener.addheaders=[
        ('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3542.0 Safari/537.36')
    ]
    urllib.request.install_opener(opener)
    ssl._create_default_https_context = ssl._create_unverified_context

    # Eliminate the end of line delimiter
    word = word.splitlines()[0]
    if word == '':
        return None
    wordUrlEncode = urllib.parse.quote(word, safe='')

    hj_Url = 'https://dict.hjenglish.com/jp/jc/{}'.format(wordUrlEncode)
    hj_Content = urllib.request.urlopen(hj_Url).read()
    hj_Soup = BeautifulSoup(hj_Content, 'lxml')
    
    Forvo_Soup = BeautifulSoup('<tag>123</tag>', 'lxml')
    Forvo_Url = 'https://forvo.com/word/{}/#ja'.format(wordUrlEncode)
    ForvoNotFound = False
    try:
        Forvo_Content = urllib.request.urlopen(Forvo_Url).read()
        Forvo_Soup = BeautifulSoup(Forvo_Content, 'lxml')
    except:
        print(' ')
        print('<< Forvo word not found!!! >>')
        print(' ')
        ForvoNotFound = True

    wordDetailsContent = hj_Soup.find('section', class_ = 'word-details-content')
    if wordDetailsContent != None:
        for wordDetailsPane in wordDetailsContent.find_all('div', class_ = 'word-details-pane'):
            word = getWord(wordDetailsPane)
            if ForvoNotFound:
                front_word += word + '<br>'
            else:
                front_word += getForvoSound(Forvo_Soup, download_dir, word) + word + '<br>'
            detailGroups = wordDetailsPane.find('section', class_ = 'detail-groups')
            if detailGroups != None:
                for posSoup in detailGroups.find_all('dl'):
                    frontAndBack = getPartOfSpeechBlock(posSoup, sentenceCnt, front_word, back_word)
                    front_word = frontAndBack['front_word']
                    back_word = frontAndBack['back_word']
            differentWord += 1
            print(' ')
            print('<< {} >>'.format(word))
            print(' ')
            print('front_word', front_word)
            print('back_word', back_word)
        result['front_word'] = front_word
        result['back_word'] = HanziConv.toTraditional(back_word)
        result['read_word'] = ''
        return result
    elif hj_Soup.find('div', class_ = 'word-suggestions') != None:
        print(' ')
        print('<< Word not found!!! >>')
        print(' ')
        return None