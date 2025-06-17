import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
import urllib3
import time
import json
import pickle


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #ignore cert stuff. this is an internal job so its ok.

# API setup
host = ""

api_headers = pickle.load( open( "session/sessionLogin.p", "rb"))
print(api_headers)
print("Logged in still!..")

INFLUXDB_URL = ""
INFLUXDB_TOKEN = ""
INFLUXDB_ORG = ""
INFLUXDB_BUCKET = ""

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
# Fetch node stats
url = f"https://{host}/rest/v1/Node"
response = requests.get(url, headers=api_headers, verify=False)  # Disables SSL verification, use if needed!


if response.status_code == 200:
    data = response.json()
    #print(f"data json: \n {data}")
    # Process each node with a new write API instance
    for node in data:
        write_api = client.write_api()
        # Create a single Write API instance
        #write_api = client.write_api(write_options=WriteOptions(batch_size=1))
        
        uuid = node["uuid"] # Use lanIP as the name
        lanIP = node["lanIP"]
        cpu_usage = node["cpuUsage"]
        z = round(cpu_usage, 3)
        mem_usage = node["memUsagePercentage"]

       ######## DEBUG STUFF, you can delete it ! #########
        #        print(f">> Stats: --")
            #        print(f"UUID:      {uuid}")
            #        print(f"IP:        {lanIP}")
            #        print(f"CPU Usage: {cpu_usage}")
            #        print(f"Mem Usage: {mem_usage}")


            # Print or process the information
                #            print(f"Node UUID: {uuid}")
                #            print(f"  Drive UUID: {drive_uuid}")
                #            print(f"  Temp: {da_temp}")
                #            print(f"  Healthy?: {health}")
                #            print(f"  Slot: {slot}")
                #            print(f"  Serial Number: {serial_number}")
                #            print(f"  Capacity: {capacity / 1e12:.2f} TB")
                #            print(f"  Used Space: {used_space / 1e12:.2f} TB")
                #            print(f"  Block Device Path: {block_device}")
                #            print("-" * 10)
            
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
            print(f"uploaded drive {slot} information for {lanIP}")
        print(f"uploaded {lanIP}")


        # Flush and close write API after processing each VM
        write_api.flush()
        write_api.close()

    print(f"Data written to InfluxDB successfully, for SCALE Cluster.")

else:
    print("Failed to fetch VM stats:", response.status_code, response.text)

# Close InfluxDB client after all VMs are processed
client.close()
