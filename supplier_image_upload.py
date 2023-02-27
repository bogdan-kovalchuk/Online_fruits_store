#!/usr/bin/env python3

import os
import requests

url = "http://localhost/upload/"
user = os.getenv('USER')
images_path = '/home/{}/supplier-data/images/'.format(user)
for image in os.listdir(images_path):
    if image.endswith('jpeg'):
        image_path = os.path.join(images_path, image)
        image_path_without_ext = os.path.splitext(image_path)[0]
        out_image_path = '{}.jpeg'.format(image_path_without_ext)
        with open(image_path, 'rb') as opened:
            r = requests.post(url, files={'file': opened})
