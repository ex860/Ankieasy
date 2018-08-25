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

def LookUp(word, download_dir):
    result = {}

    # Eliminate the end of line delimiter
    word = word.splitlines()[0]
    wordUrl = urllib.parse.quote(word, safe='')
    url='http://jisho.org/search/{}'.format(wordUrl)
    content = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(content, 'lxml')
    front_word = ''
    back_word = ''
    furi = ''
    furiChild = []
    furiList = []
    text = ''
    textChild = []
    textList = []
    reading = ''
    cnt = 0

    opener=urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    ssl._create_default_https_context = ssl._create_unverified_context

    if word == '':
        return None
        
    wrongSpelling = soup.find('div', id='no-matches')
    if wrongSpelling is not None:
        return None
    
    print(' ')
    print('<<'+word+'>>')
    print(' ')

    exactBlock = soup.find('div', class_='exact_block')
    if exactBlock == None:
        exactBlock = soup.find('div', class_='concepts')
    firstBlock = exactBlock.find('div', class_='concept_light clearfix')
    partJP = firstBlock.find('div', class_='concept_light-wrapper')
    partEN = firstBlock.find('div', class_='concept_light-meanings')
    status = partJP.find('div', class_='concept_light-status')
    if status != None:
        audio = status.find('audio')
        if audio != None and bool(download_dir) != False:
            source = audio.find('source')
            if source != None and source['src'] != None:
                try:
                    # Download the sound media to the media folder
                    urllib.request.urlretrieve('http:'+source['src'], download_dir+'Jp_'+word+'.mp3')
                    # Insert the sound media into the card
                    front_word += '[sound:Jp_'+word+'.mp3]'
                except urllib.error.HTTPError as err:
                    print('Jisho_err=', err)
    front_word += word + '<br>'
    
    furiBlock = partJP.find('span', class_='furigana')
    rubyBlock = furiBlock.find('ruby', class_='furigana-justify')
    if rubyBlock is not None:
        furiList = rubyBlock.find('rt').get_text()
    else:
        furiCnt = 0
        for child in furiBlock.children:
            furiChild.append(child.string)
            furiCnt += 1
        furiList = list(filter(('\n').__ne__, furiChild))

    textBlock = partJP.find('span', class_='text')
    textCnt = 0
    for child in textBlock.children:
        textChild.append(child.string)
        textCnt += 1
    for i in range(0, len(textChild)):
        for chr in _unicode_chr_splitter( textChild[i] ):
            if chr != '\n' and chr != ' ' and chr != '':
                textList.append(chr)
    
    if len(furiList) != len(textList):
        reading = ''
    else:
        for i in range(0, len(textList)):
            if furiList[i] == None:
                reading += textList[i] 
            else:
                reading += ' ' + textList[i] + '[' + furiList[i] + ']' 
                
    for i in partEN.find_all('div', class_='meanings-wrapper'):
        for j in i.find_all('div', class_='meaning-wrapper'):
            cnt = cnt + 1
            back_word += str(cnt) + '. '
            for q in j.find_all('span', class_='meaning-meaning'):
                back_word += q.get_text() + '<br>'

    result['read_word'] = reading
    result['front_word'] = front_word
    result['back_word'] = back_word
    return result
