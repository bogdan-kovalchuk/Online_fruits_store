#!/usr/bin/env python3

import argparse
import os
import sys
import requests
import config
import validation

HTTP_TIMEOUT = 30


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Upload JPEG images to server.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without uploading")
    return parser.parse_args(argv)


def upload_images(images_path, url, dry_run=False, timeout=HTTP_TIMEOUT):
    config.validate_url(url)
    results = []
    for image_name in sorted(os.listdir(images_path)):
        if os.path.splitext(image_name)[1].lower() in {'.jpeg', '.jpg'}:
            image_path = os.path.join(images_path, image_name)
            img_errors = validation.validate_image_file(image_path)
            if img_errors:
                results.append(("skip", image_name, "; ".join(img_errors)))
                continue
            if dry_run:
                results.append(("dry-run", image_name, url))
            else:
                try:
                    with open(image_path, 'rb') as opened:
                        r = requests.post(url, files={'file': opened}, timeout=timeout)
                    if r.status_code >= 400:
                        results.append(("error", image_name, "HTTP {}".format(r.status_code)))
                    else:
                        results.append(("uploaded", image_name, r.status_code))
                except requests.exceptions.Timeout:
                    results.append(("error", image_name, "timeout after {}s".format(timeout)))
                except requests.exceptions.ConnectionError:
                    results.append(("error", image_name, "connection error"))
                except requests.exceptions.RequestException as e:
                    results.append(("error", image_name, str(e)))
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
    has_errors = False
    for action, name, detail in results:
        if action == "skip":
            print("Skipping {}: {}".format(name, detail))
        elif action == "dry-run":
            print("Would upload: {} -> {}".format(name, detail))
        elif action == "error":
            print("Error uploading {}: {}".format(name, detail), file=sys.stderr)
            has_errors = True
        else:
            print("Uploaded {} (status {})".format(name, detail))
    if has_errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
