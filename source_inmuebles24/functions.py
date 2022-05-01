import smart_open
import spintax
import js2py
import json
import sys
import csv
import os

# Parse json from js variable
def parse_json(data):
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

# Parms for send request to webscrapingapi
def api_params(url):

    params = {
      "api_key": os.environ["api_key"],
      "url":url,
      "render_js":"1",
    }
    return params

# Create message for send contact
def format_message(msg, post, phone):
    if msg != "":
        spin = spintax.spin(msg)
        format = spin.replace("[","{").replace("]","}")
        return format.format(
                      nombre = post["publisher"],
                      titulo = post["title"],
                      precio = post["price"],
                      zona   = post["zona"],
                      sitio = "hola.ml",
                      referencia="xxx",
                      telefono=phone
                     )
    else:
        return ""

def read_bucket():
    key = os.environ["bucket_key"],
    secret_key = os.environ["bucket_secret"],
    bucket = os.environ["bucket"],
    file = os.environ["filename"],

    f = smart_open.open(f"s3://{key}:{secret_key}@{bucket}{file}", encoding='ISO-8859–1')

    a = [{k: str(v) for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]
    return a


print(os.environ["api_key"])
print(os.environ["bucket_secret"])
print(os.environ["bucket"])
print(os.environ["filename"])
