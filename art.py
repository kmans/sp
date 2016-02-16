import xml.etree.ElementTree as et
import urllib2


# url for south park xml data api
url = "http://thetvdb.com"
apiurl = "api/477ED6F3EE1F4932/series/75897/default"


def artSearch(quote):
    xmlfile = "{}/{}/{}/{}".format(url, apiurl, quote['season'], quote['episode'])
    request = urllib2.Request(xmlfile, headers={"Accept": "application/xml"})
    print xmlfile
    u = urllib2.urlopen(request)
    tree = et.parse(u)
    root = tree.getroot()
    # art = xmldoc.getElementsByTagName('filename')
    art = root.find('filename').text
    artfile = "{}/banners/{}".format(url, art)
    return artfile
