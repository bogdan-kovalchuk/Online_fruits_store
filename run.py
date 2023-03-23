#!/usr/bin/env python3

import os
import requests
import config
import validation

url = config.DEFAULT_FRUIT_URL
user = config.get_user()
descriptions_path = config.get_descriptions_path(user)
for description in os.listdir(descriptions_path):
    if description.endswith('txt'):
        description_path = os.path.join(descriptions_path, description)
        file_errors = validation.validate_description_file(description_path)
        if file_errors:
            print("Skipping {}: {}".format(description, "; ".join(file_errors)))
            continue
        lines = open(description_path,'r').read().split('\n')
        image = os.path.splitext(description)[0] + ".jpeg"
        lines = lines[:3]
        lines.append(image)
        keys = ["name", "weight", "description", "image_name"]
        json_object = dict(zip(keys, lines))
        json_object["weight"] = int(json_object["weight"].split()[0])
        data_errors = validation.validate_description_data(json_object)
        if data_errors:
            print("Skipping {}: {}".format(description, "; ".join(data_errors)))
            continue
        r = requests.post(url, data=json_object)
