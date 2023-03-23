#!/usr/bin/env python3

import argparse
import os
import sys
import requests
import config
import validation


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Upload fruit descriptions.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without making requests")
    return parser.parse_args(argv)


def process_descriptions(descriptions_path, url, dry_run=False):
    results = []
    for description in os.listdir(descriptions_path):
        if description.endswith('txt'):
            description_path = os.path.join(descriptions_path, description)
            file_errors = validation.validate_description_file(description_path)
            if file_errors:
                results.append(("skip", description, "; ".join(file_errors)))
                continue
            lines = open(description_path, 'r').read().split('\n')
            image = os.path.splitext(description)[0] + ".jpeg"
            lines = lines[:3]
            lines.append(image)
            keys = ["name", "weight", "description", "image_name"]
            json_object = dict(zip(keys, lines))
            json_object["weight"] = int(json_object["weight"].split()[0])
            data_errors = validation.validate_description_data(json_object)
            if data_errors:
                results.append(("skip", description, "; ".join(data_errors)))
                continue
            if dry_run:
                results.append(("dry-run", description, json_object))
            else:
                r = requests.post(url, data=json_object)
                results.append(("posted", description, r.status_code))
    return results


def main(argv=None):
    args = parse_args(argv)
    url = config.DEFAULT_FRUIT_URL
    user = config.get_user()
    descriptions_path = config.get_descriptions_path(user)
    dir_errors = validation.validate_directory(descriptions_path, "Descriptions path")
    if dir_errors:
        for e in dir_errors:
            print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)
    results = process_descriptions(descriptions_path, url, dry_run=args.dry_run)
    for action, name, detail in results:
        if action == "skip":
            print("Skipping {}: {}".format(name, detail))
        elif action == "dry-run":
            print("Would post: {} -> {}".format(name, detail))
        else:
            print("Posted {} (status {})".format(name, detail))


if __name__ == "__main__":
    main()
