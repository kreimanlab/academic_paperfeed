import pycurl
import html
import urllib.request
import datetime
import re
import random
from io import BytesIO

# color theme for 'dark' and 'light' terminals
THEME = 'dark'
# file containing RSS urls
RSS_URL_FILE = 'rss_urls'
# numer of items to show
N_SHOW_LINES = 1000
# maximum number of description characters to show
MAX_DESCRIPTION_LEN = 150
# if nonzero, will randomly shuffle news dates with std equal to this value
MAX_DAYS_HISTORY = 4*7

class bcolor:
    if (THEME == 'light'):
        DATE = '\033[38;5;25m'
        TITLE = '\033[38;5;166m'
        DESC = '\033[38;5;236m'
        LINK = '\033[38;5;240m'
        BRACKET = '\033[38;5;88m'
        PUB = '\033[38;5;60m'

    elif (THEME == 'dark'):
        DATE = '\033[38;5;45m'
        TITLE = '\033[38;5;208m'
        DESC = '\033[38;5;253m'
        LINK = '\033[38;5;247m'
        BRACKET = '\033[38;5;138m'
        PUB = '\033[38;5;138m'

def printHeadline(outlist):
    outstr = ""
    outstr = outstr + bcolor.DATE + '-' + outlist[0] + '-\033[49m '
    outstr = outstr + bcolor.BRACKET + '[' + bcolor.TITLE + html.unescape(outlist[1]) + bcolor.BRACKET + ']'
    outstr = outstr + bcolor.DESC + ' ' + html.unescape(outlist[2]) + '. '
    if (len(outlist) > 4):
        outstr = outstr + bcolor.PUB + '' + outlist[4] + '. '
    outstr = outstr + bcolor.LINK + '' + outlist[3] + ' '

    print(outstr)

def parseItem(itemstr, rss_v):
    itemList = []
    if (rss_v == 2):
        try:
            date = carveRSS(itemstr,'<pubDate>','</pubDate>', rss_v)[0].split()
        except:
            date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S").split()

        try:
            dnumsort = datetime.datetime.strptime(' '.join(date[1:-1]),"%d %b %Y %H:%M:%S")
        except:
            # plos
            try:
                dnumsort = datetime.datetime.strptime(date[0][0:-1],"%Y-%m-%dT%H:%M:%S")
            except:
                # international journal of computer vision 
                dnumsort = datetime.datetime.strptime(date[0][:],"%Y-%m-%d")

        try:
            dnum = datetime.datetime.strptime(' '.join(date[1:]),"%d %b %Y %H:%M:%S %Z")
        except ValueError:
            try:
                dnum = datetime.datetime.strptime(' '.join(date[1:]),"%d %b %Y %H:%M:%S %z")
            except:
                try:
                    dnum = datetime.datetime.strptime(' '.join(date[1:-1]),"%d %b %Y %H:%M:%S")
                except:
                    dnum = dnumsort
    elif(rss_v == 1):
        try:
            date = carveRSS(itemstr,'<dc:date>','</dc:date>', rss_v)[0]
            date = date.split()[0]
        except:
            date = datetime.date.today().strftime("%Y-%m-%d")
        date_tz = date[-6:]
        date_tz = date_tz.replace(':','')
        date = date[0:-6] + date_tz
        date2 = date[0:-6]
        try:
            dnumsort = datetime.datetime.strptime(date2,"%Y-%m-%dT%H:%M:%S")
            dnum = datetime.datetime.strptime(date,"%Y-%m-%dT%H:%M:%S%z")
        except:
            try:
                dnumsort = datetime.datetime.strptime(date,"%Y-%m-%d")
                dnum = datetime.datetime.strptime(date,"%Y-%m-%d")
            except:
                # Vision Research
                dnumsort = datetime.datetime.strptime(date[0:-1],"%Y-%m-%dT%H:%M%S")
                dnum = datetime.datetime.strptime(date[0:-1],"%Y-%m-%dT%H:%M%S")

    itemList.append((dnumsort - datetime.datetime(1900,1,1)).total_seconds())
    itemList.append(dnum.strftime("%b-%d-%Y %H:%M:%S GMT"))

    try:
        try:
            itemList.append(carveRSS(itemstr,'<title>','</title>',rss_v)[0].strip())
        except:
            pass
            #print('ERROR: not title found.')
        try:
            if (rss_v == 1):
                itemstr = re.sub(r'(?<=<description)(.*?)(?=>)','',itemstr)
            desc = carveRSS(itemstr,'<description>','</description>',rss_v)[0].strip()
        except:
            desc = '.'
            if (rss_v == 1):
                try:
                    desc = carveRSS(itemstr,'<content:encoded>','</content:encoded>',rss_v)[0].strip()
                except:
                    pass
                    #print('ERROR: description not found.')

        if (len(desc) > MAX_DESCRIPTION_LEN):
            desc = desc[0:MAX_DESCRIPTION_LEN]

        desc = re.sub(r'(?<=<)(.*?)(?=>)','',desc)
        desc = desc.replace('<','')
        desc = desc.replace('>','')
        itemList.append(desc)
        itemList.append(carveRSS(itemstr,'<link>','</link>',rss_v)[0].strip())

        try:
            if (rss_v == 1):
                itemList.append(carveRSS(itemstr,'<dc:publisher>','</dc:publisher>',rss_v)[0].strip())
        except:
            pass
    except:
        return []

    return itemList

def carveRSS(bodytxt, pattern_0, pattern_f, rss_v):
    if ((rss_v == 1) and (pattern_0 == '<item>')):
        #bodytxt = re.sub(r'(?<![\w\d])<items>(?![\w\d])','',bodytxt)
        #bodytxt = re.sub(r'(?<![\w\d])<\\items>(?![\w\d])','',bodytxt)
        bodytxt = re.sub(r'(?<=<item)(.*?)(?=>)','',bodytxt)
        
    bodytxt = (' '+pattern_0+' ').join(bodytxt.split(pattern_0))
    bodytxt = (' '+pattern_f+' ').join(bodytxt.split(pattern_f))
    bodylist = bodytxt.split()
    i = 0
    Outstrings = []
    start = 0
    for word in bodylist:
        if (word.startswith(pattern_0)):
            start = i
        elif (word.endswith(pattern_f)):
            linelist = bodylist[start:(i+1)]
            if (pattern_0 != '<item>'):
                linelist[0] = linelist[0].split(pattern_0)[1]
                linelist[-1] = linelist[-1].split(pattern_f)[0]
            line = ' '.join(linelist)
            if ((pattern_0 == '<description>') or (pattern_0 == '<content:encoded>')):
                line = line.split('&lt')[0]
                line = ''.join(line.split('<![CDATA['))
                line = ''.join(line.split(']]>'))
            if (pattern_0 == '<title>'):
                line = ''.join(line.split('<![CDATA['))
                line = ''.join(line.split(']]>'))
            if ('<![CDATA[' in line):
                line = ''.join(line.split('<![CDATA['))
                line = ''.join(line.split(']]>'))
            Outstrings.append(line)

        i = i + 1

    return Outstrings


def main():


    RSSall = []
    ruf = open(RSS_URL_FILE,'r')
    for l in ruf:
        lc = l.split()[0]
        if (not (lc[0] == '#')):
            RSSall.append(l.split('\n')[0])
    ruf.close()

    Feed = []

    for RSS in RSSall:
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, RSS)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        body = buffer.getvalue()
        bodytxt = body.decode('iso-8859-1')
        
        if ('rss:' in bodytxt):
            bodytxt = bodytxt.replace('rss:','')

        rss_v = 2
        Items = carveRSS(bodytxt, '<item>','</item>', rss_v)

        if not (('<rss' in bodytxt) and ('version="2.0">' in bodytxt)):
            rss_v = 1
            Items = carveRSS(bodytxt, '<item>','</item>', rss_v)

        if ('</feed>' in bodytxt):
            bodytxt = bodytxt.replace('<entry>','<item>')
            bodytxt = bodytxt.replace('</entry>','</item>')
            bodytxt = bodytxt.replace('<published>','<pubDate>')
            bodytxt = bodytxt.replace('</published>','</pubDate>')
            bodytxt = bodytxt.replace('<content type="html">','<description>')
            bodytxt = bodytxt.replace('</content>','</description>')

            bodytxt = re.sub(r'(?<=<link)(.*?)(?=>)','',bodytxt)
            bodytxt = bodytxt.replace('<link>','<link>.</link>')
            rss_v = 2
            Items = carveRSS(bodytxt, '<item>','</item>', rss_v)


        for item in Items:
            #print(item)
            pitem = parseItem(item, rss_v)
            #print(pitem)
            #exit()
            if (pitem):
                Feed.append(pitem)

    random.seed()
    rand_range_secs = MAX_DAYS_HISTORY*24*60*60
    for i in range(len(Feed)):
        Feed[i][0] = Feed[i][0] + random.gauss(0,rand_range_secs)
    Feed = sorted(Feed,key=lambda l:l[0], reverse=False)
    prev = ""
    total = len(Feed)
    print("\033c")
    for i in range(total):
        if (i > (total - N_SHOW_LINES - 1) ):
            thing = Feed[i]
            if (thing[2] == prev):
                pass
            else:
                try:
                    printHeadline(thing[1:])
                except:
                    pass
            prev = thing[2]

main()
