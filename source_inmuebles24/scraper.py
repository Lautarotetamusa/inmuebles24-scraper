from bs4 import BeautifulSoup
from threading import Thread
from . import functions
import requests
import random
import string
import time
import json
import csv
import re

site = 'https://www.inmuebles24.com'
api_url = "https://api.webscrapingapi.com/v1"
view_url = "https://www.inmuebles24.com/rp-api/leads/view"
contact_url = "https://www.inmuebles24.com/rp-api/leads/contact"
header = {'Content-Type': 'application/json'}

posts = []

# Obtain features from ad
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

# Obtener la data de una publicacion
def get_posting(card, data, postings, msg):
    features = get_features(card)
    id = card['data-id']

    location   = postings[id]['location']
    price_data = postings[id]['priceOperationTypes'][0]['prices'][0]

    post = {
        'destacado':    features['destacado'],
        'title':        features['title'],
        'zona':         location['name'],
        'ciudad':       location['parent']['name'],
        'provinicia':   location['parent']['parent']['name'],
        'publisher':    postings[id]['publisher']['name'],
        'price':        price_data['amount'],
        'currency':     price_data['currency'],
        'terreno':      features['Area'],
        'recamaras':    features['Bedrooms'],
        'banios':       features['Bathrooms'],
        'garage':       features['Garage'],
        'whatsapp':     postings[id]['whatsApp'].replace(' ', ''),
        'url':          features['url'],
    }

    # Si no ponemos nada como mensaje solamente se ve el telefono
    if msg == "":
        publisher = ver_telefono(id, postings[id]['publisher']['publisherId'])
    else: # Sino enviamos el mensaje
        # Format mensaje
        publisher = contacto(id, postings[id]['publisher']['publisherId'], post, msg, data)

    if publisher != None:
        post['phone'] = publisher['phone']
        post['publisher'] = publisher['username']
        post['cellPhone'] = publisher['cellPhone']

    posts.append(post)

# Contactar a un publisher
sending = []
def contacto(postingId, publisherId, post, msg, data):

    detail_data = {
        "email":data['email'],
        "name": data['name'],
        "phone":data['phone'],
        "page":"Listado",
        "publisherId":publisherId,
        "postingId": postingId
    }

    publisher = None
    txt = functions.format_message(msg, post, data['phone'])
    while publisher == None:
        status = 000
        while status != 200 and publisher == None:
            detail_data["message"] = txt

            res = requests.post(api_url, params=functions.api_params(contact_url), json=detail_data)
            status = res.status_code
            print('Contacting publisher', status, postingId, res.elapsed.total_seconds())
            pass

        s = BeautifulSoup(res.text, 'html.parser')
        publisher = json.loads(s.find('pre').text)['publisherOutput']

        # SI el publisher es NONE es porque ya se envio un mensaje igual a este publisher
        if publisher == None:
            # Agregamos un string random al final del mensaje
            print("Mensaje repetido, reenviando")
            change = msg + "\n\n"+"".join(random.choice(string.digits) for i in range(10))
            txt = functions.format_message(change, post, data['phone'])

    sending.append(detail_data)
    return publisher

# Ver telefono de una publicacion
def ver_telefono(postingId, publisherId):
    letters = string.ascii_letters
    digits  = string.digits

    # Genera random name, phone, email
    detail_data = {
        "name": ''.join(random.choice(letters) for i in range(10)),
        "phone":''.join(random.choice(digits)  for i in range(10)),
        "email":''.join(random.choice(letters) for i in range(10))+"@gmail.com",
        "postingId": postingId,
        "page":"Listado",
        "publisherId": publisherId
    }

    # Send post request
    status = 000
    while status != 200:
        res = requests.post(api_url, params=functions.api_params(view_url), json=detail_data)
        status = res.status_code
        print('View phone', status, res.elapsed.total_seconds())
        pass

    s = BeautifulSoup(res.text, 'html.parser')
    publisher = json.loads(s.find('pre').text)['publisherOutput']

    return publisher

# Reescribir la URL pasada para que no de error al buscarla
def parse_url(filter):
    filter = filter.replace('.html', '')

    splitted = filter.split('-q-')
    query = ''
    if(len(splitted) > 1):
        query = '-q-'+splitted[1]
    return site + '/' + splitted[0] + '-pagina-{}' + query + '.html'

# Extraer la informacion de todas las paginas
def extract(list_url, message):

    page = 1
    total_pages = page

    # Leer el archivo csv con emails y nombres
    lines = functions.read_bucket()

    while page <= total_pages:
        status = 000
        while status != 200:
            res = requests.get(api_url, params=functions.api_params(list_url.format(page)), headers=header)
            status = res.status_code
            print('PAGE nro:', page, status, res.elapsed.total_seconds())
            pass

        if page == 1:
            total_pages = functions.get_paging(res.text)

        postings = functions.parse_json(res.text)

        soup  = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all(class_="postingCard")
        if cards != []:
            start = time.time()

            threads = [Thread(target=get_posting, args=(cards[i], lines[i%len(lines)], postings, message)) for i in range(0, len(cards))]
            for t in threads:            # start the threads
                t.start()
                time.sleep(0.5)          # esperamos para evitar respuestas 429(Too many requests)
            [t.join() for t in threads]  # block until all threads finish

            print("time: ", time.time() - start)
        else:
            print('Bad url')
            break

        page += 1

#message = "Hola {[nombre]|que tal como estás?|como te va?}, {vi tu publicación|estaba viendo una publicación tuya} [titulo] con precio de [precio], {vi que está en la zona|y me di cuenta que estaba en la zona} [zona], {quiero hacerte una propuesta y quiero más información| tengo unas dudas y quiero preguntarte unas cosas| tengo unas dudas y me gustaría pregunta unos puntos importantes} te dejo mi sitio web [sitio] y la referencia [referencia] para seguir en contacto, este mes en temas legales de escrituración te propongo hacerlo con un descuento para agilizar la operación. Gracias, te paso mi whatsapp por si tienes dudas: [telefono]"

#url = parse_url("departamentos-en-renta-q-buenos-aires.html")
#extract(url, message)



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
