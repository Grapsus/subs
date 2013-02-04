#!/usr/bin/env python

import sys, os
import urllib, urllib2
from zipfile import ZipFile

from BeautifulSoup import BeautifulSoup

URL_BASE = "http://subscene.com"
URL_SEARCH = "http://subscene.com/subtitles/release.aspx?"
TMP_ZIP = '/tmp/subscene.zip'
SUB_EXTS = ('.srt')
MOV_EXTS = ('.mkv', '.avi')
LANGS = ('english', 'french')

def search(q):
    """ search for subtitles by release name """
    opener = urllib2.build_opener()
    page = opener.open(URL_SEARCH + urllib.urlencode({'q':q}))
    soup = BeautifulSoup(page)
    if str(soup).find('No results found') != -1:
        raise Exception("no results")
    content = soup('div', {'class':'content'})[0]
    for tr in content('tr'):
        td = tr('td')
        if len(td) != 5:
            continue
        
        out = {}
        # name, lang and link
        a = td[0]('a')
        if len(a) == 0:
            continue

        out['link'] = URL_BASE + a[0]['href']
        out['lang'] = a[0]('span')[0].contents[0].strip()
        out['name'] = a[0]('span')[1].contents[0].strip()
        
        # files
        out['files'] = int(td[1].contents[0].strip())

        # HI
        out['hi'] = (td[2]['class'] == 'a41')
        
        # author
        out['autor'] = td[3]('a')[0].contents[0].strip()
        
        # comments
        out['comments'] = td[4]('div')[0].contents[0].strip()

        yield out

def download(res, outfile):
    """ download subtitles from result res to outfile prefix """
    opener = urllib2.build_opener()
    page = opener.open(res['link'])
    soup = BeautifulSoup(page)
    url = URL_BASE + soup('a', {'id': 'downloadButton'})[0]['href']
    zipfile = opener.open(url)
    with open(TMP_ZIP, 'w') as tmpzip:
        tmpzip.write(zipfile.read())
    z = ZipFile(TMP_ZIP)
    for f in z.namelist():
        (filename, ext) = os.path.splitext(f)
        ext = ext.lower()
        if ext in SUB_EXTS:
            z.extract(f)
            break
    os.unlink(TMP_ZIP)
    os.rename(f, outfile + ext)

def get_release(name):
    """ get release name from filename """
    (filename, ext) = os.path.splitext(name)
    if ext.lower() in MOV_EXTS:
        return os.path.basename(filename)
    else: # already a release name
        return name

if __name__ == '__main__':
    # TODO handle hearing impaired
    # handle selection if multiple results ok
    # handle results with more than one file

    if len(sys.argv) < 2:
        sys.stderr.write("usage: %s release_or_file [langage]\n" % sys.argv[0])
        sys.exit(1)
    release = get_release(sys.argv[1].strip())

    if len(sys.argv) >= 3:
        lang = sys.argv[2].lower().strip()
    else:
        lang = LANGS[0]
    if lang not in LANGS:
        sys.stderr.write("unrecognized langage %s\n" % lang)
        sys.exit(1)
    
    res_ok = [res for res in search(release)
             if res['lang'].lower() == lang and not res['hi'] and
             res['name'].lower() == release.lower() and res['files'] == 1]

    if len(res_ok) == 0:
        sys.stderr.write("no suitable subtitles for %s in %s\n" % (release,
            lang))
        sys.exit(1)
    
    download(res_ok[0], release)
