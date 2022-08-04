import spintax
import smart_open
import csv

#--------------AUX functions------------
def get_senders(config):

    uri = f"s3://{config['key']}:{config['secret_key']}@{config['bucket_name']}{config['filename']}"

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

#---------------------------------------
