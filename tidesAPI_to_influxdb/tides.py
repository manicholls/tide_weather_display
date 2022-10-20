#!/usr/bin/python

import os
import requests
import json
from datetime import datetime
from datetime import timedelta
from influxdb import InfluxDBClient

influxdb_url = ''
influxdb_port = 8086
influxdb_user = ''
influxdb_pass = ''
tides_db = 'tides_wlp'
station_code = '5cebf1e03d0f4a073c4bbe9f'

#pip install influxdb required

today = datetime.now().strftime("%Y-%m-%d")
tomorrow = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

base_url = "https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/{0}/data?".format(station_code)
params = dict()
params["time-series-code"] = "wlp"
params["from"] = "{}T00:00:00Z".format(today)
params["to"] = "{}T00:00:00Z".format(tomorrow)

r = requests.get(base_url, params=params)

for item in r.json():
    json_body = [
      {
        "measurement": "tides_wlp",
        "time": item['eventDate'],
        "fields": {
            "value": item['value']
        }
      }
    ]
    client = InfluxDBClient(influxdb_url, influxdb_port, influxdb_user, influxdb_pass, tides_db)
    client.create_database(tides_db)
    client.write_points(json_body)

print("Script completed")
