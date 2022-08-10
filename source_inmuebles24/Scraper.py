from . import api_requests, functions
import random2
import string

site = 'https://www.inmuebles24.com'
view_url = "https://www.inmuebles24.com/rp-api/leads/view"
list_url = "https://www.inmuebles24.com/rplis-api/postings"
contact_url = "https://www.inmuebles24.com/rp-api/leads/contact"


def get_phone(post, api_params, sender, msg=""):
    detail_data = {
        "email":sender['email'],
        "name": sender['name'],
        "phone":sender['phone'],
        "page":"Listado",
        "publisherId":post['publisher']['id'],
        "postingId": post["id"]
    }


    if msg == "":
        #View the phone but not send message
        return api_requests.post(view_url, detail_data, api_params, 'View phone: ')['publisherOutput']
    else:
        #Send a message and get the phone
        while True:
            detail_data["message"] = functions.format_message(msg, post, sender)

            publisher = api_requests.post(contact_url, detail_data, api_params, "Contacting publisher: ")['publisherOutput']

            print(detail_data["message"])
            # SI el publisher es NONE es porque ya se envio un mensaje igual a este publisher
            if publisher == None:
                # Agregamos un string random2 al final del mensaje
                print("Mensaje repetido, reenviando")
                msg += "\n\n"+"".join(random2.choice(string.digits) for i in range(10))
            elif "mailerror" in publisher: #The sender mail is wrong and server return a 500 code
                return None
            else:
                #El mensaje se envio con exito, devolvemos el publisher
                return publisher


#Get the all the postings in one search
def get_postings(filters, api_params, bucket_params, msg=""):

    last_page = False
    page = 1

    #Get the senders data from S3 bucket
    sender_i = 0
    senders = functions.get_senders(bucket_params)

    posts = []
    while not last_page:
        data = api_requests.post(list_url, filters, api_params, f"Page nro: {page}")

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
            sender = senders[sender_i%len(senders)]
            publisher = get_phone(post, api_params, sender, msg)
            sender_i += 1

            if publisher != None:
                post['publisher']['phone'] = publisher['phone']
                post['publisher']['cellPhone'] = publisher['cellPhone']

            posts.append(post)

        page += 1
        filters["pagina"] = page
        last_page = data["paging"]["lastPage"]

        print("Total api calls: ",  api_requests.api_calls)
        print("Succes api calls: ", api_requests.succes_api_calls)
        print("Succes percent: ",   api_requests.succes_api_calls / api_requests.api_calls * 100)

    return posts
