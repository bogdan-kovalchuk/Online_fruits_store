#!/usr/bin/env python3

import os
from PIL import Image

user = os.getenv('USER')
images_path = '/home/{}/supplier-data/images/'.format(user)
for image in os.listdir(images_path):
    if image.endswith('tiff'):
        image_path = os.path.join(images_path, image)
        image_path_without_ext = os.path.splitext(image_path)[0]
        out_image_path = '{}.jpeg'.format(image_path_without_ext)
        image = Image.open(image_path)
        image.convert("RGB").resize((600, 400)).save(out_image_path, "JPEG")
