import xml.etree.ElementTree as et
import urllib2
import string

# url for south park xml data api
url = "http://thetvdb.com"
apiurl = "api/477ED6F3EE1F4932/series/75897/default"


def tvdbSearch(quote):
    xmlfile = "{}/{}/{}/{}".format(url, apiurl, quote['season'], quote['episode'])
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


# Eventually this should be toggled on/off, but since I need to maintain professionalism - I've defaulted this in.
# Profanity list courtesy of https://raw.githubusercontent.com/jared-mess/profanity-filter/master/bad_words.txt
def profanityFilter(results):
    badwords = [line.strip('\n') for line in urllib2.urlopen('https://gist.githubusercontent.com/kmans/75e73d5df9664049ed3a/raw/0d300a8272ceb76de8c5b809706e98902d4f020f/badwords.txt')]
    for result in results:
        print result
        filtered = result['line'].split()
        result['line'] = " ".join(map(lambda q: "*"*len(q) if q.encode('utf-8').translate(None, string.punctuation) in badwords else q, filtered))
    return results
