from lxml import html
import requests
import re
import datetime
import sys
import codecs

url = 'http://woerterbuchnetz.de/cgi-bin/WBNetz/call_wbgui_py_from_form'
db = 'RhWB'
mode = 'Volltextsuche'
txtPat = 'frz'
seiten = 3  #134
fileName = 'demo.csv'
log = 'errorlog.txt'
wortarten = [('Interj.', 'Interjektion'),
             ('m.', 'Maskulinum'),
             ('n.', 'Neutrum'),
             ('f.', 'Femininum'),
             ('Adv.', 'Adverb'),
             ('Adj.', 'Adjektiv')]


def extract_name(t):
    erster = t.xpath('//*[@id="wbarticle"]/span[1]')[0]
    zweiter = t.xpath('//*[@id="wbarticle"]/span[2]')[0]
    if erster.classes and "rhwbleitwortboldbase" in erster.classes and erster.text:
        return erster.text.strip(' ').strip(',').strip(':')
    elif zweiter.classes and "rhwbleitwortboldbase" in zweiter.classes and zweiter.text:
        return zweiter.text.strip(' ').strip(',').strip(':')
    else:
        res = ''
        for elem in tree.xpath('//div[@id="wbarticle"]/span'):
            if elem.classes and 'rhwbformrectebase' in elem.classes:
                break
            else:
                res += elem.text
        return res.strip(' ').strip(',').strip(':')


def extract_topo(t):
    res = []
    cur = ''
    for elem in tree.xpath('//div[@id="wbarticle"]/span'):
        if elem.classes and ('rhwbkompergspacedbase' in elem.classes
                             or 'rhwblemmaspacedbase' in elem.classes
                             or 'rhwbnumrectebase' in elem.classes
                             or 'rhwbleitwortboldbase' in elem.classes):
            continue

        if elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes \
                and elem.text and ':' not in elem.text and ';' not in elem.text:
            cur += elem.text

        elif elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes\
                and elem.text and ';' in elem.text:
            tmp = re.split('([;])', elem.text)
            if len(tmp)>1:
                cur += tmp[0].replace(';', '')
            res.append(cur)
            if len(tmp)>2:
                cur = tmp[2].replace(';', '')
            else:
                cur = ''

        elif elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes\
                and elem.text and ':' in elem.text:
            tmp = re.split(' ([\w.]+):', elem.text)
            if len(tmp)<2:
                tmp = re.split('([:])', elem.text)
            cur += tmp[0].replace(';', '')
            res.append(cur)
            break

    res = [x.strip(' ') for x in res]
    res = list(filter(None, res))

    return res


def extract_laut(t):
    res = []
    cur = ''
    for elem in tree.xpath('//div[@id="wbarticle"]/span'):
        if elem.classes and ('rhwbkompergspacedbase' in elem.classes
                             or 'rhwblemmaspacedbase' in elem.classes
                             or 'rhwbnumrectebase' in elem.classes
                             or 'rhwbleitwortboldbase' in elem.classes):
            continue

        if elem.classes and 'rhwbkopfinfositalicsbase' in elem.classes:
            cur += elem.text.replace(';', '')

        elif elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes \
                and elem.text and ';' in elem.text:
            res.append(cur)
            cur = ''

        elif elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes \
                and elem.text and ':' in elem.text:
            res.append(cur)
            break

    res = [x.strip(' ').strip('') for x in res]
    res = list(filter(None, res))
    return res


# Wenn das nicht direkt vorm ":" steht, dann gibts entweder keins oder das hängt wieder vom Ort ab
# (zB. obs m oder w ist). Deswegen ist das dann in einem vorherigen Span. Das wird ignoriert
def extract_wortart(t):
    for elem in tree.xpath('//div[@id="wbarticle"]/span'):
        if elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes \
                and elem.text and ':' in elem.text:
            res = re.search(' ([\w.]+):', elem.text)
            if res:
                return res.group(1)
            else:
                return ""

    return ""


def extract_dt(t):
    res = ''
    cont = True
    for elem in tree.xpath('//div[@id="wbarticle"]/span'):
        if cont and elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes \
                and elem.text and ':' in elem.text:
            cont = False

        elif cont:
            continue

        elif not cont and elem.text and txtPat in elem.text:
            tmp = re.split('('+txtPat+')', elem.text)
            if len(tmp) > 1 and txtPat not in tmp[0]:
                res += tmp[0].replace(';', '')
            break

        elif elem.text:
            res += elem.text

    return res.replace(';', '').replace('', '').replace('', '')


def extract_fr(t):
    res = ''
    cont = True
    for elem in tree.xpath('//div[@id="wbarticle"]/span'):
        if cont and elem.classes and 'rhwbkopfinfositalicsbase' not in elem.classes \
                and elem.text and txtPat in elem.text:
            cont = False

        elif cont:
            continue

        elif not cont and elem.classes and ('rhwbkompergspacedbase' in elem.classes
                                            or 'rhwblemmaspacedbase' in elem.classes
                                            or 'rhwbnumrectebase' in elem.classes
                                            or 'rhwbleitwortboldbase' in elem.classes):
            break

        elif elem.text:
            res += elem.text

    return res.replace(';', '').replace('', '').replace('', '')


def extract(t, req, lemId):
    name = extract_name(t)
    topo = '"'+'\n'.join(extract_topo(t))+'"'
    laut = '"'+'\n'.join(extract_laut(t))+'"'
    vorgeschlwortart = extract_wortart(t)
    wortart = ''
    dt = extract_dt(t)
    fr = extract_fr(t)

    matching = [x for x in wortarten if x[0] == vorgeschlwortart]
    if len(matching)>0:
        wortart = matching[0][1]
        vorgeschlwortart = ''

    if name != "":
        print(name)
        sys.stdout.flush()
        f = open(fileName, "a")  #codecs.open(fileName, "a", "utf-8")  #open(fileName, "a")
        f.write((name + ';'
                + topo + ';'
                + laut + ';'
                + wortart + ';'
                + vorgeschlwortart + ';'
                + dt + ';'
                + fr + ';'
                + '=HYPERLINK("'+req+'","'+lemId+'")' + ';' + '\n').encode('utf8').decode('utf-8'))
    else:
        print('Skipped '+req)
        sys.stdout.flush()
        f = open(log, "a")
        f.write(req + '\n')


f = open(fileName, "w")
f.write('Lemma;Topografie;Lautschrift;Wortart;Vorgeschlagene Wortarten;dt. Bedeutung;fr. Herkunft;Link;\n')
f = open(log, "w")
f.write(str(datetime.datetime.now())+'\n')

hrefs = []

for i in range(seiten):
    req = url+'?sigle='+db+'&mode='+mode+'&textpattern='+txtPat+'&firsthit='+str(i*10)
    page = requests.get(req)
    tree = html.fromstring(page.text.encode(encoding='utf-8'))
    hrefs += tree.xpath('//table[@class="hitlist"]/tr/td[@class="hitlemma"]/a/@href')

for href in hrefs:
    lemId = re.search('lemid=(\w+)', href).group(1)
    req = url+'?sigle='+db+'&lemid='+lemId
    page = requests.get(req)
    tree = html.fromstring(page.content)
    extract(tree, req, lemId)

