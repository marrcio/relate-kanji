from bs4 import BeautifulSoup
import urllib.request
import urllib.parse

USER_AGENTS = ['Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0;  rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
    ]

def scrape_table(url, dict_output=False, **kwargs):
    with urllib.request.urlopen(url) as response:
        soup = BeautifulSoup(response.read())
    scraped_data = []
    table = soup.find(**kwargs)
    headers = [header.text for header in table.find_all('th')] #may be empty
    rows = table.find_all('tr')
    for row in rows:
        entries = row.find_all('td')
        if entries:
            scraped_data.append([entry.text for entry in entries])
    if dict_output:
        scraped_data = [dict(zip(headers, entries)) for entries in scraped_data]
    return scraped_data

def get_formation_method(kanji):
    url = 'http://www.yellowbridge.com/chinese/character-etymology.php?zi='
    url += urllib.parse.quote(kanji)
    req = urllib.request.Request(url, headers={
                                 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                 })
    with urllib.request.urlopen(req) as response:
        soup = BeautifulSoup(response.read(), "html.parser")
    try:
        fm = soup.find(id='formation').find_all('tr')[1].find('ol').text
    except:
        fm = "FAIL"

    return (kanji, fm)

def scrape_kanji(kanji):
    url = 'https://en.wiktionary.org/wiki/'
    url += urllib.parse.quote(kanji)
    with urllib.request.urlopen(url) as response:
        soup = BeautifulSoup(response.read(), "html.parser")
    try:
        ans = soup.select('#Han_character')[0].parent.findNextSibling('p').text
    except:
        ans = ''
        problems.append(kanji)
        print('Problem with kanji ' + kanji)
    return ans
