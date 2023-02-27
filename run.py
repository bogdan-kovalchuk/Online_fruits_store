#!/usr/bin/env python3

import os
import requests

url = "http://34.133.132.84/fruits/"
user = os.getenv('USER')
descriptions_path = '/home/{}/supplier-data/descriptions/'.format(user)
for description in os.listdir(descriptions_path):
    if description.endswith('txt'):
        description_path = os.path.join(descriptions_path, description)
        lines = open(description_path,'r').read().split('\n')
        image = os.path.splitext(description)[0] + ".jpeg"
        lines = lines[:3]
        lines.append(image)
        keys = ["name", "weight", "description", "image_name"]
        json_object = dict(zip(keys, lines))
        json_object["weight"] = int(json_object["weight"].split()[0])
        r = requests.post(url, data=json_object)
