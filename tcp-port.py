#! /usr/bin/env python3

import csv
import os
import re

import requests


URL = "https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv"
CACHE_FILE = "tcp-port-iana.csv"
OUTPUT_FILE = "tcp-port.csv"
COLUMNS = ["Port", "Service", "Description"]
PORT_RANGE = re.compile(r"^(\d+)-(\d+)$")


def get_cache_file(cache_file, url):
    cache_file = os.path.join(os.path.dirname(__file__), ".cache", cache_file)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    if not os.path.exists(cache_file):
        r = requests.get(url)
        r.raise_for_status()
        open(cache_file, "w").write(r.text)
    return cache_file


def scrape_port(port_number, service_name, description, ports={}):
    description = description.splitlines()[0] if description else ""
    if description.lower() == "unassigned":
        return
    prior = ports.get(port_number)
    prior_description = prior[COLUMNS.index("Description")] if prior else description
    if description != prior_description:
        print("Description mismatch - port", port_number)
        print(repr(prior_description))
        print(repr(description))
        print()
    ports[port_number] = [port_number, service_name, description]


def scrape_all():
    ports = {}
    with open(get_cache_file(CACHE_FILE, URL), newline="") as csvfile:
        reader = csv.reader(csvfile)
        for header_row in reader:
            break
        for row in reader:
            service_name = row[0]
            description = row[3]
            port_spec = row[1]
            port_range = PORT_RANGE.match(port_spec)
            if port_range:
                minport = int(port_range.group(1))
                maxport = int(port_range.group(2))
                for port_number in range(minport, maxport + 1):
                    scrape_port(port_number, service_name, description, ports)
            elif port_spec:
                port_number = int(port_spec)
                scrape_port(port_number, service_name, description, ports)
    return [row for _, row in sorted(ports.items())]


def write_csv(ports):
    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        wr = csv.writer(csvfile, lineterminator="\n")
        wr.writerow(COLUMNS)
        for port_row in ports:
            wr.writerow(port_row)


if __name__ == "__main__":
    write_csv(scrape_all())
