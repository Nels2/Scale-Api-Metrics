import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
import urllib3
import time
import json
import pickle

api_headers = pickle.load( open( "session/sessionLogin.p", "rb"))
print(api_headers)
print("Logged in still!..")
host=""
logout_url = f"https://{host}/rest/v1/logout"
logout_response = requests.request("POST",
                                   logout_url,
                                   headers=api_headers,
                                   verify=False
)
print("Closing Session!")
print(logout_response)
print(">> Session is closed.")

