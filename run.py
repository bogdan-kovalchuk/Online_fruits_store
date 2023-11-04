#!/usr/bin/env python3

import argparse
import json
import os
import sys
import requests
import config
import validation

HTTP_TIMEOUT = 30
DEFAULT_STATE_FILE = os.path.join(tempfile.gettempdir(), "fruit_store_state.json") if False else "/tmp/fruit_store_state.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Upload fruit descriptions.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without making requests")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE,
                        help="Path to idempotency state file")
    return parser.parse_args(argv)


def load_state(state_file):
    if not state_file or not os.path.isfile(state_file):
        return {"posted": []}
    with open(state_file, 'r') as f:
        return json.load(f)


def save_state(state_file, state):
    parent = os.path.dirname(state_file)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f)


def process_descriptions(descriptions_path, url, dry_run=False, timeout=HTTP_TIMEOUT, state=None):
    config.validate_url(url)
    if state is None:
        state = {"posted": []}
    posted_names = set(state.get("posted", []))
    results = []
    for description in sorted(os.listdir(descriptions_path)):
        if description.endswith('txt'):
            if description in posted_names:
                results.append(("already-posted", description, "skipped (idempotent)"))
                continue
            description_path = os.path.join(descriptions_path, description)
            file_errors = validation.validate_description_file(description_path)
            if file_errors:
                results.append(("skip", description, "; ".join(file_errors)))
                continue
            with open(description_path, 'r') as f:
                lines = f.read().split('\n')
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
                try:
                    r = requests.post(url, data=json_object, timeout=timeout)
                    if r.status_code >= 400:
                        results.append(("error", description, "HTTP {}".format(r.status_code)))
                    else:
                        results.append(("posted", description, r.status_code))
                        state.setdefault("posted", []).append(description)
                except requests.exceptions.Timeout:
                    results.append(("error", description, "timeout after {}s".format(timeout)))
                except requests.exceptions.ConnectionError:
                    results.append(("error", description, "connection error"))
                except requests.exceptions.RequestException as e:
                    results.append(("error", description, str(e)))
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
    state = load_state(args.state_file) if not args.dry_run else {"posted": []}
    results = process_descriptions(descriptions_path, url, dry_run=args.dry_run, state=state)
    has_errors = False
    for action, name, detail in results:
        if action == "skip":
            print("Skipping {}: {}".format(name, detail))
        elif action == "dry-run":
            print("Would post: {} -> {}".format(name, detail))
        elif action == "already-posted":
            print("Already posted {}: {}".format(name, detail))
        elif action == "error":
            print("Error posting {}: {}".format(name, detail), file=sys.stderr)
            has_errors = True
        else:
            print("Posted {} (status {})".format(name, detail))
    if not args.dry_run:
        save_state(args.state_file, state)
    if has_errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
