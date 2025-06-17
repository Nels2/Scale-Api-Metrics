import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
import urllib3
import time
import json


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




client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)



# Fetch node stats
response = requests.get(url, headers=rest_opts, verify=False)  # Disable SSL verification if needed


if response.status_code == 200:
    data = response.json()
    #print(f"data json: \n {data}")
    # Process each node with a new write API instance

    


    # Process each node
    for node in data:
        write_api = client.write_api()
        
        uuid = node["uuid"] # Use lanIP as the name
        lanIP = node["lanIP"]
        cpu_usage = node["cpuUsage"]
        z = round(cpu_usage, 3)
        mem_usage = node["memUsagePercentage"]
        
            
        print(f"found {lanIP} - CPU@{cpu_usage} || MEM@{mem_usage} || {z}....")
        time.sleep(3)
        # CPU metrics
        cpu_point = (
            Point("cpu") 
            .tag("node", lanIP) 
            .field("usage", round(cpu_usage, 3)) 
        )
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, cpu_point)

        # Memory metrics
        mem_point = (
            Point("memory") 
            .tag("node", lanIP) 
            .field("usage(%)", mem_usage) 
        )
        write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, mem_point)

        # Disk metrics
        for drive in node.get("drives", []):
            drive_uuid = drive["uuid"]
            slot = drive["slot"]
            health = drive["isHealthy"]
            serial_number = drive["serialNumber"]
            da_temp = drive["temperature"]
            capacity = drive["capacityBytes"]
            used_space = drive["usedBytes"]
            block_device = drive["blockDevicePath"]

            disk_point = (
                Point("disk") 
                .tag("node", lanIP) 
                .tag("device", slot) 
                .tag("path", block_device)
                .field("SN", serial_number) 
                .field("isHealthy", health) 
                .field("temperature", da_temp) 
                .field("used", used_space) 
                .field("health_status", 1 if health == "True" else 0) 
            )
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, disk_point)
            print(f"uploaded drive {slot} for {lanIP}")
        print(f"uploaded {lanIP}")


        # Flush and close write API after processing each VM
        write_api.flush()
        write_api.close()

    print(f"Data written to InfluxDB successfully, for SCALE Cluster.")

else:
    print("Failed to fetch VM stats:", response.status_code, response.text)

# Close InfluxDB client after all VMs are processed
client.close()
