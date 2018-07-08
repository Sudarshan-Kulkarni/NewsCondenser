import requests
#from pws import Google
from bs4 import BeautifulSoup
import re
from nltk.sentiment.vader import    SentimentIntensityAnalyzer as SIA
from pprint import pprint


def dispdict(di):
    for key in di:
        print(key,':',di[key])

def linkclean(tlinks):
    links = []
    for link in tlinks:
        if link.startswith('/url?q='):
            links.append(link[7:link.find('&')])
        else:
            links.append(link[:link.find('&')])
    flinks = []
    for link in links:
        if link not in flinks:
            flinks.append(link)

    return flinks

def gettitle(links):
    titles = []
    print('Retrieving the headlines from various sources.')
    for link in links:
        r = requests.head(link)
        if r.status_code<400:
            print('Visiting',link,'status code:',r.status_code)
            r = requests.get(link)
            html = r.text
            soup = BeautifulSoup(html,'html.parser')
            #print(soup.find('title').text)
            if(soup.find('title')):
                titles.append(soup.find('title').text)
            else:
                links.remove(link)

    titles = [title.strip()  for title in titles if not (title == 'Terms of Service Violation' or title == 'Error Page')]
    return titles

def visiturl(url):
    print('Visiting',url)
    r = requests.head(url)
    if r.status_code < 400:
        r = requests.get(url)
        html = r.text
        soup = BeautifulSoup(html,'html.parser')
        return soup
    else:
        print('The URL isn\'t valid')

def getmarketwatchinfo(linkext):
    info = {}
    soup = visiturl('https://www.marketwatch.com' + linkext)
    #print(soup.find('div',attrs = {'class':"intraday__close"}))
    el = soup.find('td',attrs = {'class':"table__cell u-semi"}).text
    info['Last Trade Price'] = el
    #print(info['Last Price'])
    el = soup.find_all('td',attrs = {'class':["table__cell not-fixed positive","table__cell not-fixed negative"]})
    info['Change %'] = el[1].text
    #print(info['chg %'])
    table = soup.find_all('li',attrs = {'class':"kv__item"})
    el = False
    for row in table:
        name = row.find('small',attrs = {'class':"kv__label"}).text
        if name == 'Market Cap':
            el = row.find('span',attrs = {'class':"kv__value kv__primary "}).text

    if(el):
        info['Market Cap'] = el
        #print(info['Market Cap'])
    info['Current Price'] = soup.find('bg-quote',attrs = {'class':"value"}).text
    #print(info['Current Price'])
    return info

def getmoneycontrolinfo():
    url = 'https://www.moneycontrol.com/stocks/marketinfo/marketcap/nse/computers-software.html'
    soup = visiturl(url)
    #print(soup.find_all('a',attrs = {'class':"bl_12"}))
    rlinks = soup.find_all('a',attrs = {'class':"bl_12"})
    linkext = "/india/stockpricequote/computerssoftware/"+(''.join(company)).lower()
    f = False
    for link in rlinks:
        if linkext in link.get('href'):
            linkext = link.get('href')
            f = True
    if f == False:
        print("The requested company's information wasn't available on moneycontrol.com or you haven't entered the correct name")
        return False
    #print(linkext)
    soup = visiturl('https://www.moneycontrol.com'+linkext)
    #print(soup.find('title').text)
    info = {}
    #print(soup.find('div',attrs = {'id':"b_prevclose"}).text)
    info['Last Trade Price'] = soup.find('div',attrs = {'id':"b_prevclose"}).text
    #print(soup.find('div',attrs = {'id':"b_bidprice_qty"}).text)
    info['Current Bid Price'] = soup.find('div',attrs = {'id':"b_bidprice_qty"}).text
    #print(soup.find('div',attrs = {'id':"Bse_Prc_tick_div"}).text)
    info['Current Price'] = soup.find('div',attrs = {'id':"Bse_Prc_tick_div"}).text
    #print(soup.find('div', attrs={'id': "b_changetext"}).text)
    change = (soup.find('div', attrs={'id': "b_changetext"}).text).split()
    chgpercent= change[1][1:-1]
    #print(chgpercent)
    info['Change %'] = chgpercent
    #print(soup.find('div',attrs = {'class':"FR gD_12"}).text)
    marketcap = soup.find('div',attrs = {'class':"FR gD_12"}).text
    info['Market Cap'] = marketcap
    return info

def analyzer(titles,links):
    sia = SIA()
    analysis = []
    for title in titles:
        score = sia.polarity_scores(title)
        score['Headline'] = title
        analysis.append(score)

    #pprint(analysis,width = 100)
    #print the good sentiment links
    poslinks = []
    neglinks = []
    for score in analysis:
        if score['compound']>=0.4:
            poslinks.append(links[analysis.index(score)])
        elif score['compound']<=-0.3:
            neglinks.append(links[analysis.index(score)])
    if(poslinks):
        print('Here are some links that highlight the positive sentiment of the media towards the company')
        for link in poslinks:
            print(link)
    else:
        print('No headlines pertaining to the company are positive today,try again later')
    if(neglinks):
        print('Here are some links that highlight the negative sentiment of the media towards the company')
        for link in neglinks:
            print(link)
    else:
        print('No headlines pertaining to the company are negative today,try again later')








#getting the name of the company and visiting google news
query = input("Enter the name of the company.")
print("Accepted")
query = query.split()
company = query
query = '+'.join(query)

url = "https://www.google.com/search?q="+query+"&num=10&start=0&tbm=nws#q="+query+"&tbas=0&tbs=sbd:1&tbm=nws&gl=d"
r = requests.get(url)

#getting the response and converting it into a soup to extract the links
html = r.text
soup = BeautifulSoup(html,"html.parser")
#print(soup.prettify())
#print(soup.find_all('a'))

#extracting the links
links = []
for link in soup.findAll('a',attrs = {'href':re.compile("^[/url?q=]*http[s]*://")}):
    links.append(link.get('href'))
#print(links)
tlinks = [l for l in links if not('google.co.in' in l or 'google.com' in l or 'youtube.com' in l)]
#print(tlinks)

#cleaning the links
links = linkclean(tlinks)
print(links)

titles = gettitle(links)
for title in titles:
    print(title)

#get the market stats for the company,from marketwatch.
soup = visiturl('https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup='+query+'&Country=us&Type=All')
#print(soup.find('a',attrs = {'title':re.compile('^'+company[0].capitalize())}))
element = soup.find('a',attrs = {'title':re.compile('^'+company[0].capitalize())})
if(element):
    linkext = element.get('href')
    #print(linkext)
    marketwatchinfo = getmarketwatchinfo(linkext)
    dispdict(marketwatchinfo)

else:
    print("The requested company's information wasn't available on marketwatch.com or you haven't entered the correct name")


#get the market stats for the company from moneycontrol
moneycontrolinfo = getmoneycontrolinfo()
if (moneycontrolinfo):
    dispdict(moneycontrolinfo)

#analyze the headlines by putting the titles in the analyser

print("Analyzing the headlines")
analyzer(titles,links)





