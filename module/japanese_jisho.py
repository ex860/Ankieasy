import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup
import ssl
import subprocess
import platform
import datetime
import json
import re
import base64
from re import compile as _Re

_unicode_chr_splitter = _Re( '(?s)((?:[\u2e80-\u9fff])|.)' ).split

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
            if author in ['skent', 'akitomo', 'kaoring', 'kyokotokyojapan', 'kiiro', 'yasuo', 'sorechaude', 'Phlebia']:
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

def LookUp(word, download_dir):
    result = {}

    # Eliminate the end of line delimiter
    word = word.splitlines()[0]
    wordUrl = urllib.parse.quote(word, safe='')
    url='http://jisho.org/search/{}'.format(wordUrl)
    content = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(content, 'lxml')

    Forvo_Soup = BeautifulSoup('<tag>123</tag>', 'lxml')
    Forvo_Url = 'https://forvo.com/word/{}/#ja'.format(wordUrl)
    ForvoNotFound = False
    try:
        Forvo_Content = urllib.request.urlopen(Forvo_Url).read()
        Forvo_Soup = BeautifulSoup(Forvo_Content, 'lxml')
    except:
        print(' ')
        print('<< Forvo word not found!!! >>')
        print(' ')
        ForvoNotFound = True

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
    if ForvoNotFound:
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
    else:
        front_word += getForvoSound(Forvo_Soup, download_dir, word) + word + '<br>'
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
