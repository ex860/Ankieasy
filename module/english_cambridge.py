import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup
import ssl
import subprocess
import platform
import datetime
import json
import re

def LookUp(word, download_dir):

    # Eliminate the end of line delimiter
    word = word.splitlines()[0]
    wordUrl = urllib.parse.quote(word, safe='')
    wordUrl = wordUrl.replace('%20','-')
    wordUrl = wordUrl.replace('%27','-')
    wordUrl = wordUrl.replace('%28','-')
    wordUrl = wordUrl.replace('%29','-')
    wordUrl = wordUrl.replace('%2F','-')
    wordUrl = wordUrl.replace('--','-')
    if wordUrl[-1] == '-':
        wordUrl = wordUrl[:-1]
    
    url='https://dictionary.cambridge.org/us/dictionary/english-chinese-traditional/{}'.format(wordUrl)

    opener=urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    ssl._create_default_https_context = ssl._create_unverified_context

    content = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(content, 'lxml')
    result = {}
    front_word = word + '<br>'
    back_word = ''
    guideWordStyleHead = '<font color="yellow"><b>'
    guideWordStyleTail = '</b></font>'
    posStyleHead = '<font color=#00fff9>'
    posStyleTail = '</font>'
    soundCnt = 1
    cnt = 1

    if word == '':
        return None

    for posBlock in soup.select('div.pr.entry-body__el'):                           # posBlock means the part of speech block of the word
        for pos in posBlock.select('span.pos.dpos'):
            front_word += "{}({}){}<br>".format(posStyleHead, pos.get_text(), posStyleTail)
            back_word += "{}({}){}<br>".format(posStyleHead, pos.get_text(), posStyleTail)
            # print(pos.get_text())
        for usAudio in posBlock.select('span.us.dpron-i'):
            for source in usAudio.select('source[type="audio/mpeg"]'):
                if source is not None and bool(download_dir) != False:
                    try:
                        urllib.request.urlretrieve('https://dictionary.cambridge.org{}'.format(source['src']), '{}Py_{}_{}.mp3'.format(download_dir, word, soundCnt))
                        front_word = '[sound:Py_{}_{}.mp3]'.format(word, soundCnt) + front_word
                        soundCnt = soundCnt + 1
                    except urllib.error.HTTPError as err:
                        print("HTTP Error:", err)
                    # print(source['src'])
        for guideWordBlock in posBlock.select('div.pr.dsense'):                     # There can be more than one guide word in a part of speech
            for guideword in guideWordBlock.select('span.guideword.dsense_gw'):
                back_word += "{}{}{}<br>".format(guideWordStyleHead, guideword.get_text(), guideWordStyleTail)
                # print(guideword.get_text())
            for meaningBlock in guideWordBlock.select('div.def-block.ddef_block'):  # A guide word can include many meanings
                for enMeaning in meaningBlock.select('div.def.ddef_d'):
                    back_word += "{}) {}<br>".format(cnt, enMeaning.get_text())
                    # print(enMeaning.get_text())
                for zhMeaning in meaningBlock.select('div.def-body.ddef_b > span.trans.dtrans.dtrans-se'):
                    back_word += "{}) {}<br>".format(cnt, zhMeaning.get_text())
                    # print(zhMeaning.get_text())
                front_word += "{}) ".format(cnt)
                for enExample in meaningBlock.select('div.def-body.ddef_b > div.examp.dexamp > span.eg.deg'):
                    front_word += "{}".format(enExample.get_text())
                    # print(enExample.get_text())
                    break
                front_word += "<br>"
                for zhExample in meaningBlock.select('div.def-body.ddef_b > div.examp.dexamp > span.trans.dtrans.dtrans-se.hdb'):
                    back_word += "{}<br>".format(zhExample.get_text())
                    # print(zhExample.get_text())
                    break
                cnt += 1
            # print('-------------------------')
        # print('●●●●●●●●●●●●●●●●●●●●●●●●●●')

    # Some meaning will reveal the 'word' in back_word
    back_word = back_word.replace(word,'___')
    uppercase_word = word[0].upper() + word[1:len(word)]
    back_word = back_word.replace(uppercase_word,'___')

    result['front_word'] = front_word
    result['back_word'] = back_word
    print(' ')
    print('<< {} >>'.format(word))
    print(' ')
    print('front_word', front_word)
    print('back_word', back_word)
    return result
