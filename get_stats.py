import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
import urllib3
import time
import json
import pickle


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #ignore cert stuff. this is an internal job so its ok.
host = ""


## New login method ----
api_headers = pickle.load( open( "session/sessionLogin.p", "rb"))
print(api_headers)
print("Logged in Still!..")

# InfluxDB setup
INFLUXDB_URL = ""
INFLUXDB_TOKEN = ""
INFLUXDB_ORG = ""
INFLUXDB_BUCKET = ""

# Function to get VM name from the external API using the UUID
def get_vm_name(vm_uuid):
    url = f"https://{host}/rest/v1/VirDomain/{vm_uuid}"
    print(f"Trying... {url}")

    try:
        # Make the request (use GET if API expects GET)
        response = requests.request("GET", url, headers=api_headers, verify=False)

        # Check if response is successful
        response.raise_for_status()

        # Get the response content
        response_text = response.text

        # Debug: print raw response
        #print(f"Response text: {response_text}")

        # If response is empty, return None
        if not response_text:
            print("Empty response received.")
            return None

        # Parse JSON
        response_json = response.json()  # requests.Response object has a .json() method

        #print(response_json)

        # Assuming response_json is a list of dicts, get the first item's name
        if isinstance(response_json, list) and response_json:
            print(">> Successfully found data for: " + response_json[0]["name"])
            return response_json[0]["name"]
        else:
            print("Unexpected JSON format or empty list.")
            return None

    except requests.RequestException as e:
        print(f"Error fetching VM name for {vm_uuid}: {e}")
        return None
    except ValueError as ve:
        # JSON decoding failed
        print(f"JSON decode error: {ve}")
        return None


client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)


# Fetch VM stats
url = f"https://{host}/rest/v1/VirDomainStats" #blanket fetch VMs
response = requests.get(url, headers=api_headers, verify=False)  # Disable SSL verification if needed

if response.status_code == 200:
    data = response.json()
    for vm in data:
        vm_uuid = vm["uuid"]
        #print(f">> Using {vm_uuid}...")
        vm_name = get_vm_name(vm_uuid)

        # Skip if VM name is not found
        if not vm_name:
            print(f"Skipping VM with UUID {vm_uuid} as the name could not be retrieved.")
            continue

        #print(">>> Pausing script to see if data is right...") #DEBUG
        #time.sleep(6000) #DEBUG


        # Open a new write API instance for each VM
        write_api = client.write_api(write_options=WriteOptions(batch_size=1))

        # Ensure float conversion
        cpu_usage = float(vm["cpuUsage"])
        rx_bit_rate = float(vm["rxBitRate"])
        tx_bit_rate = float(vm["txBitRate"])

        # Write VM-level stats
        vm_point = (
            Point("vm_metrics")
            #
            .tag("vm_name", vm_name)
            .tag("vm_uuid", vm_uuid) #old way
            .field("cpu_usage", vm["cpuUsage"])
            .field("rx_bit_rate", vm["rxBitRate"])
            .field("tx_bit_rate", vm["txBitRate"])
            .time(None, WritePrecision.NS)
        )
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, vm_point)

        # Write disk-level stats
        for vsd in vm.get("vsdStats", []):
            disk_uuid = vsd["uuid"]

            for rate in vsd.get("rates", []):
                disk_point = (
                    Point("disk_stats")
                    .tag("vm_uuid", vm_uuid)
                    .tag("vm_name", vm_name)  # Use VM name here
                    .tag("disk_uuid", disk_uuid)
                    .field("milliwrites_per_second", float(rate["milliwritesPerSecond"]))
                    .field("millireads_per_second", float(rate["millireadsPerSecond"]))
                    .field("read_kib_per_sec", float(rate["readKibibytesPerSecond"]))
                    .field("write_kib_per_sec", float(rate["writeKibibytesPerSecond"]))
                    .field("mean_read_latency_us", float(rate["meanReadLatencyMicroseconds"]))
                    .field("mean_write_latency_us", float(rate["meanWriteLatencyMicroseconds"]))
                    .time(None, WritePrecision.NS)
                )
                write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, disk_point)

        # Flush and close write API after processing each VM
        write_api.flush()
        write_api.close()

    print(f"Data written to InfluxDB successfully, for SCALE Cluster.")

else:
    print("Failed to fetch VM stats:", response.status_code, response.text)

# Close InfluxDB client after all VMs are processed
client.close()
