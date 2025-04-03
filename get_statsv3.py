import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
import urllib3
import time


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #ignore cert stuff. this is an internal job so its ok.

# API setup
xcred = "<SCALE GUI TOKEN>"  # For Scale GUI login
host = "<SCALE API HOST>"  # Replace with your IP/FQDN for your cluster.
url = f"https://{host}/rest/v1/Node"
credentials = f"Basic {xcred}"  
rest_opts = {
    "Content-Type": "application/json",
    "Authorization": credentials,
    "Connection": "keep-alive"
}

# InfluxDB setup
INFLUXDB_URL = "<INFLUXDB URL HERE>"  # Replace with your URL
INFLUXDB_TOKEN = "<INFLUXDB TOKEN>"   # Replace with your token
INFLUXDB_ORG = "<INFLUXDB ORG>"       # Replace with your org
INFLUXDB_BUCKET = "<INFLUXDB BUCKET>" # Replace with your bucket


# Function to get VM name from the external API using the UUID
def get_vm_name(vm_uuid):
    url = f"https://<URL>/rest/v1/VirDomain/{vm_uuid}" # Replace with URL
    print(f"Trying... {url}")
    response = requests.get(url, headers=rest_opts, verify=False)  # Disable SSL verification if needed
    
    try:
        response.raise_for_status()
        vm_data = response.json()
        print(">> Successfully found data for: " + vm_data[0]["name"])
        # Return the name of the VM
        return vm_data[0]["name"] if vm_data else None
    except requests.RequestException as e:
        print(f"Error fetching VM name for {vm_uuid}: {e}")
        return None






client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)


# Fetch VM stats
response = requests.get(url, headers=rest_opts, verify=False)  # Disable SSL verification if needed

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
        #time.sleep(60) #DEBUG


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
