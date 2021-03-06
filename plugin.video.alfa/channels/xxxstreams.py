# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import scrapertools
from core import servertools
from core import httptools
from core.item import Item
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gounlimited']

######    SOLO DESCARGAS
host = 'http://xxxstreams.org' #es http://freepornstreams.org

def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Peliculas" , action="lista", url= host + "/full-porn-movie-stream/"))
    itemlist.append(item.clone(title="Videos" , action="lista", url=host + "/new-porn-streaming/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    # itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Categorias" :
        data1 = scrapertools.find_single_match(data,'>Top Tags</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'>Ethnic</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'>Kinky</a>(.*?)</ul>')
    if item.title == "Canal" :
        data1 = scrapertools.find_single_match(data,'>Top sites</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'Downloads</h2>(.*?)</ul>')
    patron  = '<a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data1)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="entry-content">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<a href="([^<]+)".*?'
    patron += '<span class="screen-reader-text">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        if '/HD' in scrapedtitle : title= "[COLOR red]HD[/COLOR] %s" % scrapedtitle
        elif 'SD' in scrapedtitle : title= "[COLOR red]SD[/COLOR] %s" % scrapedtitle
        elif 'FullHD' in scrapedtitle : title= "[COLOR red]FullHD[/COLOR] %s" % scrapedtitle
        elif '1080' in scrapedtitle : title= "[COLOR red]1080p[/COLOR] %s" % scrapedtitle
        else: title = scrapedtitle
        if not "MANYVIDS" in title or not "UBIQFILE" in title:
            itemlist.append(item.clone(action="findvideos", title=title, contentTitle=title, url=scrapedurl,
                               fanart=scrapedthumbnail, thumbnail=scrapedthumbnail,plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &rarr;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist

# https://k2s.cc/file/a4948953ebe66/Edyn_Blair_Up_and_Close_and_Personal_sd.mp4
# https://k2s.cc/file/d5445d9833d4d/Edyn_Blair_Up_and_Close_and_Personal_fullhd.mp4
# https://api.k2s.cc/v1/files/a4948953ebe66

# https://www.okstream.cc/e/e5d48e3fa183
# https://playtube.ws/embed-c0ffkg097ts9-658x400.html  packed

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" rel="nofollow[^>]+>(?:<strong>|)\s*(?:Streaming|Download)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        if not "ubiqfile" in url:
            itemlist.append(item.clone(action='play',title="%s", contentTitle=item.title, url=url))
        # else:
            # itemlist.append(item.clone(action='play',title="Descarga Ubiqfile: %s", contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

