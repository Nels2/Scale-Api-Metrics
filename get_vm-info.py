#!/usr/bin/python3
import requests
import urllib3
import time
import json
import sys
import pickle


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #ignore cert stuff. this is an internal job so its ok.
host = ""
user2use = ""
pass2use = ""


if len(sys.argv) != 2:
    print("Usage: python getmatch.py <hostname-substring>")
    sys.exit(1)

raw = sys.argv[1].strip()          # trim whitespace
# remove one leading + trailing quote char if present
if (raw.startswith(("'", '"')) and raw.endswith(("'", '"'))):
    raw = raw[1:-1]

search_term = raw.lower()

## New login method ----
def gen_session():
    api_login = f'https://{host}/rest/v1/login'

    api_headers = {
        'Content-Type': 'application/json'
        }

    login_payload = json.dumps({
        "username": user2use,
        "password": pass2use,
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

    print(f"Logged in with {api_headers}..")
    return api_headers


def kill_session():
    print(f"Logged in still, {api_headers}!..")
    logout_url = f"https://{host}/rest/v1/logout"
    logout_response = requests.request("POST",
                                    logout_url,
                                    headers=api_headers,
                                    verify=False
    )
    print("Closing Session!")
    print(logout_response)
    print(">> Session is closed.")


api_headers = gen_session()

# Function to get VM name from the external API using the UUID
def get_vm_details(vm_uuid):
    url = f"https://{host}/rest/v1/VirDomain/{vm_uuid}"
    try:
        response = requests.get(url, headers=api_headers, verify=False)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            data = data[0]
        return {
            "uuid": data.get("uuid"),
            "name": data.get("name"),
            "description": data.get("description", "")
        }
    except Exception as e:
        print(f"Failed to get details for UUID {vm_uuid}: {e}")
        return None




# Fetch VM stats
url = f"https://{host}/rest/v1/VirDomainStats" #blanket fetch VMs
response = requests.get(url, headers=api_headers, verify=False)  # Disable SSL verification if needed

if response.status_code == 200:
    found_match = False
    for vm in response.json():
        vm_uuid = vm.get("uuid")
        vm_info = get_vm_details(vm_uuid)

        if not vm_info:
            continue

        vm_name = vm_info["name"].lower()
        if search_term in vm_name:
            found_match = True
            print("\n=== MATCH FOUND ===")
            print(f"VM Name     : {vm_info['name']}")
            print(f"Description : {vm_info['description']}")
            print(f"UUID        : {vm_info['uuid']}")
            print("====================\n")
            kill_session()
            print(vm_info["uuid"])  # Final line: UUID only
            sys.exit(0)

    if not found_match:
        kill_session()
        print(f"No match found for hostname: {search_term}")
        sys.exit(1)
else:
    kill_session()
    print(f"Failed to fetch VM stats: {response.status_code}")
    sys.exit(2)
