#!/usr/bin/env python3

import argparse
import os
import sys
import requests
import config
import validation


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Upload JPEG images to server.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without uploading")
    return parser.parse_args(argv)


def upload_images(images_path, url, dry_run=False):
    results = []
    for image_name in os.listdir(images_path):
        if image_name.endswith('jpeg'):
            image_path = os.path.join(images_path, image_name)
            if dry_run:
                results.append(("dry-run", image_name, url))
            else:
                with open(image_path, 'rb') as opened:
                    r = requests.post(url, files={'file': opened})
                results.append(("uploaded", image_name, r.status_code))
    return results


def main(argv=None):
    args = parse_args(argv)
    url = config.DEFAULT_UPLOAD_URL
    user = config.get_user()
    images_path = config.get_images_path(user)
    dir_errors = validation.validate_directory(images_path, "Images path")
    if dir_errors:
        for e in dir_errors:
            print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)
    results = upload_images(images_path, url, dry_run=args.dry_run)
    for action, name, detail in results:
        if action == "dry-run":
            print("Would upload: {} -> {}".format(name, detail))
        else:
            print("Uploaded {} (status {})".format(name, detail))


if __name__ == "__main__":
    main()
