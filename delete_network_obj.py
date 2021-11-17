import requests
from requests.models import HTTPError
import meraki
import getpass
import json


base_url = "https://api.meraki.com/api/v1"


def collect_info():
    org_name = input("Please enter your Meraki Organization Name: ")
    api_key = getpass.getpass("Please enter your Meraki API key: ")
    dashboard = meraki.DashboardAPI(api_key)

    # Call Get Org function
    org_id = get_org_id(dashboard, org_name)

    return api_key, dashboard, org_id


def get_org_id(dashboard, org_name):
    orgs = dashboard.organizations.getOrganizations()

    for row in orgs:
        if row['name'] == org_name:
            org_id = row['id']
            print(f"Organization ID: {org_id}")
        else:
            raise ValueError('The organization name does not exist')

    return org_id


def list_network_obj(api_key, org_id):
    # print("List group object function")
    url = f"{base_url}/organizations/{org_id}/policyObjects/"
    try:
        payload = {}
        headers = {
                    'X-Cisco-Meraki-API-Key': api_key,
                    'Content-Type': 'application/json'
                  }

        response = requests.get(url, headers=headers, data=payload)
        print(f"List Network Object response code: {response.status_code}")  # We want a Status code of 200

        json_obj_networks = json.loads(response.text)

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")

    return json_obj_networks


def delete_network_obj(api_key, org_id):

    json_policy_obj = list_network_obj(api_key, org_id)

    delete_obj = input("Would you like to DELETE ALL policy objects in Dashboard? This IRREVERSIBLE. Please enter y or n : ")

    if delete_obj == "y":
        # Using for loop  to iterate over a list
        for d in json_policy_obj:
            policy_obj_id = d['id']
            policy_obj_name = d['name']
            print(f"Deleting policy object {policy_obj_name}")
            url = f"{base_url}/organizations/{org_id}/policyObjects/{policy_obj_id}"
            try:
                payload = {}
                headers = {
                            'X-Cisco-Meraki-API-Key': api_key,
                            'Content-Type': 'application/json'
                          }

                response = requests.delete(url, headers=headers, data=payload)
                print(response.status_code)  # We want a Status code of 204

            except HTTPError as http_err:
                print(f"An HTTP error has occured {http_err}")
            except Exception as err:
                print(f"An error has occured {err}")
        else:
            print(f"Policy Object {policy_obj_name} will NOT be removed.")


def main():
    api_key, dashboard, org_id = collect_info()
    delete_network_obj(api_key, org_id)


if __name__ == "__main__":
    main()
