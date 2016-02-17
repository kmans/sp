import xml.etree.ElementTree as et
import urllib2

# url for south park xml data api
url = "http://thetvdb.com"
apiurl = "api/477ED6F3EE1F4932/series/75897/default"


def tvdbSearch(quote):
    xmlfile = "{}/{}/{}/{}".format(url, apiurl, quote['season'], quote['episode'])
    print "XMLFILE", xmlfile
    request = urllib2.Request(xmlfile, headers={"Accept": "application/xml"})
    u = urllib2.urlopen(request)
    tree = et.parse(u)
    root = tree.getroot()
    # art = xmldoc.getElementsByTagName('filename')
    art = "".join([x.text for x in root.iter("filename")])
    episodename = "".join([x.text for x in root.iter("EpisodeName")])
    overview = "".join([x.text for x in root.iter("Overview")])
    artfile = u"{}/banners/{}".format(url, art)
    return artfile, episodename, overview
