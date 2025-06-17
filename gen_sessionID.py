import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
import urllib3
import time
import json
import pickle


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #This basically disables warning about invalid cert, you can remove this for a valid cert.
host = ""


## New login method ----

api_login = f'https://{host}/rest/v1/login'

api_headers = {
    'Content-Type': 'application/json'
    }

login_payload = json.dumps({
    "username": username
    "password": password,
    "useOIDC": False
})

login_response = requests.request("POST",
                                  api_login,
                                  headers=api_headers,
                                  data=login_payload,
                                  verify=False
                                  )

api_headers['Cookie'] = 'sessionID={0}'.format(
    login_response.cookies.get('sessionID'))

print(api_headers)
print("Logged in..")

pickle.dump( api_headers, open( "session/sessionLogin.p", "wb"))
print("Session has been pickled!")
