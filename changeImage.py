#!/usr/bin/env python3

import argparse
import os
import sys
from PIL import Image
import config
import validation


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Convert TIFF images to JPEG.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without converting images")
    return parser.parse_args(argv)


def convert_images(images_path, dry_run=False):
    results = []
    for image_name in os.listdir(images_path):
        if image_name.endswith('tiff'):
            image_path = os.path.join(images_path, image_name)
            image_path_without_ext = os.path.splitext(image_path)[0]
            out_image_path = '{}.jpeg'.format(image_path_without_ext)
            if dry_run:
                results.append(("dry-run", image_name, out_image_path))
            else:
                img = Image.open(image_path)
                img.convert("RGB").resize(
                    (config.DEFAULT_IMAGE_WIDTH, config.DEFAULT_IMAGE_HEIGHT)
                ).save(out_image_path, "JPEG")
                results.append(("converted", image_name, out_image_path))
    return results


def main(argv=None):
    args = parse_args(argv)
    user = config.get_user()
    images_path = config.get_images_path(user)
    dir_errors = validation.validate_directory(images_path, "Images path")
    if dir_errors:
        for e in dir_errors:
            print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)
    results = convert_images(images_path, dry_run=args.dry_run)
    for action, name, detail in results:
        if action == "dry-run":
            print("Would convert: {} -> {}".format(name, detail))
        else:
            print("Converted {} -> {}".format(name, detail))


if __name__ == "__main__":
    main()
