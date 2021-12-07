#
# This script is for demonstation purposes only.
# It uses Meraki Policy Object APIs to delete Network Objects


import requests
from requests.models import HTTPError
import getpass
import json
import time


base_url = "https://api.meraki.com/api/v1"


# List the organizations that the user has access to
def get_user_orgs(api_key):
    get_url = f'{base_url}/organizations'
    headers = {'X-Cisco-Meraki-API-Key': api_key,
               'Content-Type': 'application/json'
               }

    response = requests.get(get_url, headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


# Function to prompt user for API key and Org ID
def collect_info():
    print('********************DEMO********************')
    print('This script is for demo purposes only.\n')
    print('It will use Meraki APIs to DELETE Network Objects\n')
    print('********************DEMO********************\n')
    print('*********** DELETE NETWORK OBJECTS *********\n')

    # Ask for user's API key
    while True:
        api_key = getpass.getpass('If you would like to continue, please enter your Meraki API key: ')
        (ok, orgs) = get_user_orgs(api_key)
        if ok:
            break
        else:
            print('There was a problem with the API key you entered.')
    # Get organization ID and name
    org_ids = []
    org_names = []
    print('You have access to these organizations with that API key.')
    for org in orgs:
        org_id = org['id']
        org_name = org['name']
        org_ids.append(str(org_id))
        org_names.append(org_name)
        print('Organization ID\t\tOrganization Name'.expandtabs(8))
        print(f'{org_id:20}\t{org_name}')
    print()

    while True:
        # Ask for Org ID
        org_id = input('Please enter the Organization ID you would like to DELETE Objects from: ')
        if org_id in org_ids:
            break
        else:
            print('That org ID is not one listed, try another.')
    print()

    return api_key, org_id


def list_network_obj(api_key, org_id):
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
        return json_obj_networks

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")


def delete_network_obj(api_key, org_id):

    actions_lst = []
    count = 0
    batch = 0

    json_policy_obj = list_network_obj(api_key, org_id)

    if json_policy_obj:   # List is not empty - some objects found in Dashboard

        delete_obj = input("Would you like to DELETE ALL policy objects in Dashboard? This IRREVERSIBLE. Please enter y or n : ")

        if delete_obj == "y":
            # Using for loop  to iterate over a list
            for d in json_policy_obj:
                policy_obj_id = d['id']
                policy_obj_name = d['name']
                print(f"Deleting policy object {policy_obj_name}")

                url = f"/organizations/{org_id}/policyObjects/{policy_obj_id}"
                action_payload = {
                    'resource': url,
                    'operation': 'destroy',
                    'body': {}
                }
                actions_lst.append(action_payload)
                count += 1
        else:
            print("Policy Objects will NOT be removed.")
    else:
        print("There are no Policy Objects in Dashboard to delete.")

    for i in range(0, len(actions_lst), 100):  # Send 100 at a time to action batch function
        actions = actions_lst[i:i+100]
        time.sleep(1)
        batch_objects(base_url, api_key, org_id, actions)
        batch += 1

    print(f'Policy Objects DELETED from Dashboard: {count}')
    print(f'Action batches processed: {batch}')


def batch_objects(base_url, api_key, org_id, actions):
    url = f'{base_url}/organizations/{org_id}/actionBatches'

    try:
        payload = json.dumps({
            'confirmed': True,
            'synchronous': False,
            'actions': actions
        })
        headers = {
            'X-Cisco-Meraki-API-Key': api_key,
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        print(f'Action Batch response code: {response.status_code}')  # We want a Status code of 201

    except HTTPError as http_err:
        print(f'An HTTP error has occured {http_err}')
    except Exception as err:
        print(f'An error has occured {err}')
    return


def main():
    api_key, org_id = collect_info()
    delete_network_obj(api_key, org_id)


if __name__ == "__main__":
    main()
