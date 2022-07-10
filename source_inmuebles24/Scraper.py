import smart_open
import requests
import spintax
import random2
import string
import json
import csv
from bs4 import BeautifulSoup

site = 'https://www.inmuebles24.com'
view_url = "https://www.inmuebles24.com/rp-api/leads/view"
list_url = "https://www.inmuebles24.com/rplis-api/postings"
contact_url = "https://www.inmuebles24.com/rp-api/leads/contact"

api_calls = 0
succes_api_calls = 0

#--------------AUX functions------------
def read_bucket():
    key = "AKIA3YE4AEODPFIOEN4Q"#os.environ["bucket_key"],
    secret_key = "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"
    bucket_name = "inmuebles24-scraper-bucket"
    filename = "/input/data.csv"

    uri = f"s3://{key}:{secret_key}@{bucket_name}{filename}"

    f = smart_open.open(uri, encoding='ISO-8859–1')

    a = [{k: str(v) for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]
    return a
#Create message for send to contact
def format_message(msg, post, data):
    if msg != "":
        spin = spintax.spin(msg)
        format = spin.replace("[","{").replace("]","}")
        return format.format(
                      nombre = post["publisher"]["name"],
                      titulo = post["title"],
                      precio = post["price"],
                      zona   = post["location"]["zona"],
                      sitio = "hola.ml",
                      referencia="xxx",
                      telefono=data["phone"]
                     )
    else:
        return ""
#Send a POST request with webscrapingapi
def api_request(url, request, log=""):
    api_key = "RQDAOZCd4mlujy7M7JKtfvelJWEROoR1"
    api_url = "https://api.webscrapingapi.com/v1"

    params = {
      "api_key": api_key,#os.environ["api_key"],
      "url":url,
      "render_js":"1",
    }

    global api_calls
    global succes_api_calls

    while True:
        res = requests.post(api_url, params=params, json=request)
        api_calls += 1
        print(f"{log} - [status {res.status_code}] - [time {res.elapsed.total_seconds()}]")
        if res.status_code == 200:
            break
        else:
            print(res.text)

    #Get the <pre> </pre> tag
    try:
        soup = BeautifulSoup(res.text, 'html.parser')
        succes_api_calls += 1
        return json.loads(soup.find('pre').text)
    except Exception as e:
        print(e)
        print('CANT LOAD BS4 FROM PAGE')
        print("url:", url)
        print("request:", json.dumps(request, indent=4))
        exit()
#---------------------------------------

#Send message to the publisher
def contact(post, publisherId, msg, sender):

    detail_data = {
        "email":sender['email'],
        "name": sender['name'],
        "phone":sender['phone'],
        "page":"Listado",
        "publisherId":publisherId,
        "postingId": post["id"]
    }

    while True:
        detail_data["message"] = format_message(msg, post, sender)

        publisher = api_request(contact_url, detail_data, "Contacting publisher: ")['publisherOutput']

        # SI el publisher es NONE es porque ya se envio un mensaje igual a este publisher
        if publisher == None:
            # Agregamos un string random2 al final del mensaje
            print("Mensaje repetido, reenviando")
            msg += "\n\n"+"".join(random2.choice(string.digits) for i in range(10))
        else:
            #El mensaje se envio con exito, devolvemos el publisher
            print(detail_data["message"])
            return publisher
#View publisher phone
def view_phone(postingId, publisherId):
    letters = string.ascii_letters
    digits  = string.digits

    # Genera random2 name, phone, email
    detail_data = {
        "name": ''.join(random2.choice(letters) for i in range(10)),
        "phone":''.join(random2.choice(digits)  for i in range(10)),
        "email":''.join(random2.choice(letters) for i in range(10))+"@gmail.com",
        "postingId": postingId,
        "page":"Listado",
        "publisherId": publisherId
    }

    publisher = api_request(view_url, detail_data, 'View phone: ')['publisherOutput']

    return publisher

#Get the all the postings in one search
def get_postings(filters, msg=""):

    last_page = False
    page = 1

    #Get the senders data from S3 bucket
    sender_i = 0
    senders = read_bucket()

    posts = []
    while not last_page:
        data = api_request(list_url, filters, f"Page nro: {page}")

        #Scrape the data from the JSON
        for p in data['listPostings']:
            publisher  = p['publisher']

            location   = p['postingLocation']['location']
            price_data = p['priceOperationTypes'][0]['prices'][0]

            post = {
                'id':           p['postingId'],
                'title':        p['title'],
                'price':        price_data['formattedAmount'],
                'currency':     price_data['currency'],
                'type':         p['realEstateType']['name'],
                'url':          site+p['url'],
                'location':     {
                    'zona':         location['name'],
                    'ciudad':       location['parent']['name'],
                    'provinicia':   location['parent']['parent']['name'],
                },
                'publisher':    {
                    'id':           publisher['publisherId'],
                    'name':         publisher['name'],
                    'whatsapp':     p['whatsApp'],
                }
            }

            #features
            features_keys = [
                ("terreno", "CFT100"),
                ("construido", "CFT101"),
                ("recamaras", "CFT2"),
                ("banios", "CFT3"),
                ("garage", "CFT7"),
                ("antiguedad", "CFT5")]

            mainFeatures = p['mainFeatures']
            for feature, key in features_keys:
                if key in mainFeatures:
                    post[feature] = mainFeatures[key]['value']
            #-------

            #Get the publisher data
            #Si no ponemos nada como mensaje solamente se ve el telefono
            if msg == "":
                publisher = view_phone(post["id"], post['publisher']['id'])
            else: # Sino enviamos el mensaje
                # Format mensaje
                sender = senders[sender_i%len(senders)]
                sender_i += 1
                publisher = contact(post, post['publisher']['id'], msg, sender)

            if publisher != None:
                post['publisher']['phone'] = publisher['phone']
                post['publisher']['cellPhone'] = publisher['cellPhone']


            posts.append(post)

        page += 1
        filters["pagina"] = page
        last_page = data["paging"]["lastPage"]

    return posts

if __name__ == '__main__':
    """filters = {
    	"ambientesmaximo": 0,
    	"ambientesminimo": 0,
    	"amenidades": "",
    	#"antiguedad": null,
    	"areaComun": "",
    	"areaPrivativa": "",
    	#"auctions": null,
    	#"banks": null,
    	#"banos": null,
    	#"caracteristicasprop": null,
    	#"city": null,
    	"comodidades": "",
    	#"coordenates": null,
    	#"direccion": null,
    	#"disposicion": null,
    	"etapaDeDesarrollo": "",
    	#"expensasmaximo": null,
    	#"expensasminimo": null,
    	#"garages": null,
    	"general": "",
    	"grupoTipoDeMultimedia": "",
    	"habitacionesmaximo": 0,
    	"habitacionesminimo": 0,
    	#"idInmobiliaria": null,
    	"idunidaddemedida": 1,
    	#"metroscuadradomax": null,
    	#"metroscuadradomin": null,
    	#"moneda": null,
    	"multipleRets": "",
    	"outside": "",
    	"pagina": 1,
    	#"polygonApplied": null,
    	#"preciomax": null,
    	#"preciomin": null,
    	#"province": null,
    	#"publicacion": null,
    	"q": "rosario",
    	"roomType": "",
    	"searchbykeyword": "",
    	"services": "",
    	"sort": "relevance",
    	#"subtipoDePropiedad": null,
    	#"subZone": null,
    	"superficieCubierta": 1,
    	"tipoAnunciante": "ALL",
    	"tipoDeOperacion": "1",
    	"tipoDePropiedad": "2",
    	#"valueZone": null,
    	#"zone": null
    } Rosario"""

    filters = {
    	"ambientesmaximo": 0,
    	"ambientesminimo": 0,
    	"amenidades": "",
    	#"antiguedad": null,
    	"areaComun": "",
    	"areaPrivativa": "",
    	#"auctions": null,
    	#"banks": null,
    	#"banos": null,
    	#"caracteristicasprop": null,
    	"city": "2057",
    	"comodidades": "",
    	#"coordenates": null,
    	#"direccion": null,
    	#"disposicion": null,
    	"etapaDeDesarrollo": "",
    	#"expensasmaximo": null,
    	#"expensasminimo": null,
    	#"garages": null,
    	"general": "",
    	"grupoTipoDeMultimedia": "",
    	"habitacionesmaximo": 0,
    	"habitacionesminimo": 0,
    	#"idInmobiliaria": null,
    	"idunidaddemedida": 1,
    	#"metroscuadradomax": null,
    	#"metroscuadradomin": null,
    	#"moneda": null,
    	"multipleRets": "",
    	"outside": "",
    	"pagina": 2,
    	#"polygonApplied": null,
    	#"preciomax": null,
    	#"preciomin": null,
    	#"province": null,
    	#"publicacion": null,
    	#"q": null,
    	"roomType": "",
    	"searchbykeyword": "",
    	"services": "",
    	"sort": "relevance",
    	#"subtipoDePropiedad": null,
    	#"subZone": null,
    	"superficieCubierta": 1,
    	"tipoAnunciante": "ALL",
    	"tipoDeOperacion": "1",
    	"tipoDePropiedad": "3",
    	#"valueZone": null,
    	#"zone": null
    }


    msg = "Hola {[nombre]|que tal como estás?|como te va?}, {vi tu publicación|estaba viendo una publicación tuya} [titulo] con precio de [precio], {vi que está en la zona|y me di cuenta que estaba en la zona} [zona], {quiero hacerte una propuesta y quiero más información| tengo unas dudas y quiero preguntarte unas cosas| tengo unas dudas y me gustaría pregunta unos puntos importantes} te dejo mi sitio web [sitio] y la referencia [referencia] para seguir en contacto, este mes en temas legales de escrituración te propongo hacerlo con un descuento para agilizar la operación. Gracias, te paso mi whatsapp por si tienes dudas: [telefono]"

    import time
    time_start = time.time()
    posts = get_postings(filters, msg)
    print(json.dumps(posts, indent=4))
    print("extracted", len(posts), "ads in", time.time() - time_start, "seconds")

    try:
        print("api calls:", api_calls)
        print("succes api calls:", succes_api_calls)
        print("succes percentage:", (succes_api_calls / api_calls) * 100)
    except Exception as e:
        print("XDXDXD")
