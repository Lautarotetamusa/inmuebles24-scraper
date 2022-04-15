from bs4 import BeautifulSoup
from threading import Thread
import requests
import random
import string
import js2py
import time
import json
import csv
import sys
import re

site = 'https://www.inmuebles24.com'
api_url = "https://api.webscrapingapi.com/v1"
detail_url = "https://www.inmuebles24.com/rp-api/leads/view"
header = {'Content-Type': 'application/json'}

#Parse json from js variable
def parse_json(data):
    publisher_fields = ['url', 'urlLogo', 'name', 'premium', 'publisherId']

    j1 = data.split('let postingInfo = ')[1]
    j3 = j1.split('};')[0]+'}'

    js = """
        function parse_info(){
            let info = """+j3+"""
            return JSON.stringify(info);
        }
        """

    result = js2py.eval_js(js)
    return json.loads(result())

def get_paging(data):
    j1 = data.split('const paging =')[1]
    j2 = j1.split('}')[0]+'}'

    js = """
        function parse_info(){
            const paging = """+j2+"""
            return paging.totalPages;
        }
        """
    result = js2py.eval_js(js)
    return int(result())

#Parms for send request to webscrapingapi
def api_params(url):

    params = {
      "api_key":"RQDAOZCd4mlujy7M7JKtfvelJWEROoR1",
      "url":url,
      "render_js":"1",
    }
    return params

#Obtain features from ad
def get_features(card):

    temp_dict = {}
    title = card.find(class_="postingCardTitle")

    if(title is None): #La publicacion es un departamento
        title = card.find('h4', class_="go-to-posting")
        if(title is None):
            title = ''
        else:
            title = title.text
        temp_dict['url']   = site+card["data-to-posting"]
    else:
        temp_dict['url']   = site+title.find('a').get('href')
        title = title.text

    temp_dict['title'] = title.strip()

    mainFeatures = card.find(class_='postingCardMainFeatures').find_all('li')
    features = ['Area', 'Bedrooms', 'Bathrooms', 'Garage']

    try:
        temp_dict['destacado'] = card["class"][1]
    except Exception as e:
        temp_dict['destacado'] = ''

    for f in features:
        temp_dict[f] = ''

    i = 0
    for f in mainFeatures:
        if(f.i == None):
            tipo = features[i]
        else:
            tipo = f.i["class"][1].replace('icon', '')

        if tipo == 'Environments':
            tipo = 'Bedrooms'

        if tipo in features:
            temp_dict[tipo] = re.sub('[\n\t]| {2,}', '', f.text)
        else:
            temp_dict[tipo] = ''
        i+=1

    temp_dict['Bathrooms'] = ' '.join(temp_dict['Bathrooms'].split('baños'))
    temp_dict['Garage'] = ' '.join(temp_dict['Garage'].split('estac.'))

    return temp_dict

# POSTINGS
posts = []
def get_postings(card, postings):

    features = get_features(card)
    id = card['data-id']

    location   = postings[id]['location']
    price_data = postings[id]['priceOperationTypes'][0]['prices'][0]
    publisher  = get_details(id, postings[id]['publisher']['publisherId'])

    posts.append({
        'destacado':    features['destacado'],
        'title':        features['title'],
        'zona':         location['name'],
        'ciudad':       location['parent']['name'],
        'provinicia':   location['parent']['parent']['name'],
        'price':        price_data['amount'],
        'currency':     price_data['currency'],
        'terreno':      features['Area'],
        'recamaras':    features['Bedrooms'],
        'banios':       features['Bathrooms'],
        'garage':       features['Garage'],
        'publisher':    publisher['username'],
        'whatsapp':     postings[id]['whatsApp'].replace(' ', ''),
        'phone':        publisher['phone'],
        'cellPhone':    publisher['cellPhone'],
        'url':          features['url'],
    })

#DETAILS
def get_details(postingId, publisherId):
    letters = string.ascii_letters
    digits  = string.digits

    detail_data = {
        "name": ''.join(random.choice(letters) for i in range(10)),
        "phone":''.join(random.choice(digits)  for i in range(10)),
        "email":''.join(random.choice(letters) for i in range(10))+"@gmail.com",
        "postingId": postingId,
        "page":"Listado",
        "publisherId": publisherId
    }

    status = 000
    while status != 200:
        res = requests.post(api_url, params=api_params(detail_url), json=detail_data)
        status = res.status_code
        print('Requesting phone', status, res.elapsed.total_seconds())
        pass

    publisher = ''
    s = BeautifulSoup(res.text, 'html.parser')
    publisher = json.loads(s.find('pre').text)['publisherOutput']
    return publisher

#Extract
def extract(list_url):

    page = 1
    total_pages = page

    while page <= total_pages:
        status = 000
        while status != 200:
            res = requests.get(api_url, params=api_params(list_url.format(page)), headers=header)
            status = res.status_code
            print('PAGE nro:', page, status, res.elapsed.total_seconds())
            pass

        if page == 1:
            total_pages = get_paging(res.text)

        postings = parse_json(res.text)

        soup  = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all(class_="postingCard")
        if cards != []:
            start = time.time()

            threads = [Thread(target=get_postings, args=(n, postings)) for n in cards]
            for t in threads: #start the threads
                t.start()
                time.sleep(0.5) #esperamos para evitar respuestas 429(Too many requests)
            [t.join() for t in threads]  # block until all threads finish

            print("time: ", time.time() - start)
        else:
            print('Bad url')
            break

        page += 1
    return posts

def parse_url(filter):
    #filter = 'departamentos-en-venta.html'
    filter = filter.replace('.html', '')

    splitted = filter.split('-q-')
    query = ''
    if(len(splitted) > 1):
        query = '-q-'+splitted[1]
    return site + '/' + splitted[0] + '-pagina-{}' + query + '.html'

#time_start = time.time()
#url = parse_url('departamentos-en-venta-q-rosario.html')
#print(url)
#extract(url)
#print("extracted", len(posts), "ads in", time.time() - time_start, "seconds")


"""
with open('output.csv', 'w', encoding='UTF8') as f:
    writer = csv.writer(f)

    # write the header
    print(posts)
    header = posts[0].keys()#['url', 'titulo', 'zona', 'ciudad', 'provincia', 'precio', 'currency', 'terreno', 'terreno construido', 'recamaras', 'baños', 'whatsApp', 'publisher','telefono', 'celular']
    writer.writerow(header)

    # write the data
    for post in posts:
        print(post)
        writer.writerow(post.values())
"""
