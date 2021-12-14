#
# This script is for demonstation purposes only. It was not written for a
# production environment.
#
# The script uses Meraki Policy Object APIs to create and modify Network Objects/Groups.
#
# The script will import information from a .csv file
# that contains the following 5 columns:
#
# name	category	type	cidr	groupName
#
# Note:
# Object groups can not contain more than 150 policy objects.
# If the number of policy objects for group exceeds the 150 count limit,
# create an additional group(s) for excess policies.
#
# There is a sample template called object-import.csv
#
# This script is used before create_l3_fw_rules.py


import os
import requests
from requests.models import HTTPError
import getpass
import csv
import json
import copy
import time


base_url = 'https://api.meraki.com/api/v1'
#csv_file = 'object-import.csv'


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
    # Ask for user's API key

    print('********************DEMO********************')
    print('This script is for demo purposes only.\n')
    print('It will use Meraki APIs to create and modify')
    print('Network Objects/Groups\n')
    print('********************DEMO********************\n')

    while True:
        csv_file = input("Please enter the name of the .csv file containing the Group and Policy object: ")
        print()
        file_exists = os.path.exists(csv_file)
        if file_exists:
            break
        else:
            print('The file you entered does not exist.\n')

    while True:
        api_key = getpass.getpass('If you would like to continue, please enter your Meraki API key: ')
        (ok, orgs) = get_user_orgs(api_key)
        if ok:
            break
        else:
            print('There was a problem with the API key you entered.\n')

    # Get organization ID and name
    org_ids = []
    org_names = []
    print()
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
        org_id = input('Please enter the Organization ID you would like to configure: ')
        if org_id in org_ids:
            break
        else:
            print('That org ID is not one listed, try another.\n')
    print()

    return csv_file, api_key, org_id


# Function to read csv file
def read_csv(csv_file, api_key, org_id):
    object_names_lst = []
    object_groups_lst = []
    object_dict_lst = []
    linking_dict = {}
    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            # The data from four columns in the file will be used
            # The columns are name, category, type, cidr and groupName
            # Read in data from the relevant columns in the row and assign it to a variable
            for row in reader:
                name = row['name']
                category = row['category']
                type = row['type']
                cidr = row['cidr']
                group_name = row['groupName']
                
                if not name:
                    break
                # Create a 'linking' dictionary
                # This contains the policy object name and policy object group that it belongs too
                if group_name:  # If group name is not empty
                    # If there is no key with the Object Group Name create one
                    if group_name not in linking_dict:
                        linking_dict[group_name] = list()
                        linking_dict[group_name].append(name)
                    else:
                        # Key exists check if object is in the list of networks
                        if name in linking_dict[group_name]:
                            print(f'Policy Object {name} already exists in Group {group_name}')
                        else:
                            # Key exists add object not in list of networks - add it
                            linking_dict[group_name].append(name)

                # Create a list of unique Policy Group Names
                # If the group is not in the list, append it to the list
                if group_name:  # If group name is not empty
                    if group_name not in object_groups_lst:
                        # Append to list
                        object_groups_lst.append(group_name)

                # Create a list of unique Network Object Names
                # If object is not in the list then add it
                if name not in object_names_lst:
                    # append to list
                    object_names_lst.append(name)

                # Create a dictionary with the following keys
                # name, category, type, cidr, groupIds
                # Assign each key a value
                # Append the dictionary to obj_dict_lst list
                # This will be the Body of the API call
                    policy_object = {
                        'name': name,
                        'category': category,
                        'type': type,
                        'cidr': cidr,
                        'groupIds': []
                    }
                    object_dict_lst.append(policy_object)  # This will be a list of dictionaries

            print(f'UNIQUE OBJECT GROUPS: {len(object_groups_lst)}')
            print(f'UNIQUE OBJECT NAMES: {len(object_names_lst)}')
            # Call function: to determine if group object exists or needs created
            check_group_obj(api_key, object_groups_lst, org_id)

            # Call function: to determine if network object exists or needs created
            check_net_obj(api_key, object_names_lst, object_dict_lst, org_id)

            # Call function: to link network objects to group objects
            link_objects_to_groups(api_key, org_id, linking_dict)

    except IOError:
        print('I/O error')

    return


# Function to check and add group policy objects to Dashboard
def check_group_obj(api_key, obj_group_lst, org_id):
    existing_group_obj_name_lst = []
    # Check if the group object already exists using List Group function
    existing_group_obj = list_group_obj(api_key, org_id)  # This will return a list of dictionaries

    # Create list of existing object names from the list of dictionaries
    if existing_group_obj:   # List is not empty - some group objects found in Dashboard
        for item in existing_group_obj:   # Create a list of existing group object names
            name = item['name']
            # Append to list
            existing_group_obj_name_lst.append(name)

    # Search list of dictionaries to see if group object name exists
    # Create Object Group for each item in obj_group_lst

    actions_lst = []
    count = 0
    batch = 0
    for group in obj_group_lst:  # This is the list of policy group objects we want to create
        if existing_group_obj:   # Tist is not empty - some group objects found in Dashboard
            # Create Object Group for each item in obj_group_lst
            if group in existing_group_obj_name_lst:   # This is the list of policy group object names in Dashboard
                print(f'Group {group} is already configured in Dashboard.')
            else:
                print(f'Need to create group object {group}')

                action_payload = {
                    'resource': f'/organizations/{org_id}/policyObjects/groups',
                    'operation': 'create',
                    'body': {
                        'name': group
                    }
                }
                actions_lst.append(action_payload)
                count += 1

        else:   # List is empty - no network objects found in Dashboard
            action_payload = {
                'resource': f'/organizations/{org_id}/policyObjects/groups',
                'operation': 'create',
                'body': {
                    'name': group
                }
            }
            actions_lst.append(action_payload)
            count += 1
    for i in range(0, len(actions_lst), 100):  # Send 100 at a time to action batch function
        actions = actions_lst[i:i+100]
        batch_objects(base_url, api_key, org_id, actions)
        batch += 1

    print(f'Group Object Policy ADDED to Dashboard: {count}')
    print(f'Action batches GROUP ADDED processed: {batch}')
    return


# Function to list group policy objects in Dashboard
def list_group_obj(api_key, org_id):
    url = f'{base_url}/organizations/{org_id}/policyObjects/groups'

    try:
        payload = {}
        headers = {
            'X-Cisco-Meraki-API-Key': api_key,
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, data=payload)
        print(f'List Group response code: {response.status_code}')  # We want a Status code of 200

        json_obj_groups = json.loads(response.text)
        return json_obj_groups

    except HTTPError as http_err:
        print(f'An HTTP error has occured {http_err}')
    except Exception as err:
        print(f'An error has occured {err}')

    return


# Function to check and add policy objects to Dashboard
def check_net_obj(api_key, obj_names_lst, obj_dict_lst, org_id):
    existing_net_obj_lst = []

    # Check if the group object already exists using List Network Object function
    existing_net_obj = list_network_obj(api_key, org_id)  # this will return a list of dictionaries

    # Create list of existing object names from the list of dictionaries
    for i in existing_net_obj:
        name = i['name']
        # if name not in existing_net_obj
        # append to list
        existing_net_obj_lst.append(name)

    # Search list of dictionaries to see if network object name exists
    # Create Network Object for each item in obj_net_lst

    actions_lst = []
    count = 0
    batch = 0

    for network in obj_names_lst:  # This is the list of policy objects we want to create
        if existing_net_obj:   # List is not empty - network objects found in Dashboard
            #print('Existing Network Object list NOT empty')

            if network in existing_net_obj_lst:  # This is the list of policy objects in Dashboard
                print(f'Network {network} is already configured in Dashboard.')
            else:
                print(f'Need to create network object {network}')
                # Call Function to make API Call if network in obj_dict_list
                for d in obj_dict_lst:   # choose item in obj_dict_lst
                    if network == d['name']:
                        nme = d['name']
                        print(f'Network {network} Name : {nme}')
                        action_payload = {
                            'resource': f'/organizations/{org_id}/policyObjects',
                            'operation': 'create',
                            'body': {
                                'name': d['name'],
                                'category': d['category'],
                                'type': d['type'],
                                'cidr': d['cidr']
                            }
                        }
                        actions_lst.append(action_payload)
                        count += 1
        else:   # List is empty - no network objects found in Dashboard
            for d in obj_dict_lst:
                if network == d['name']:
                    action_payload = {
                        'resource': f'/organizations/{org_id}/policyObjects',
                        'operation': 'create',
                        'body': {
                            'name': d['name'],
                            'category': d['category'],
                            'type': d['type'],
                            'cidr': d['cidr']
                        }
                    }
                    actions_lst.append(action_payload)
                    count += 1

    for i in range(0, len(actions_lst), 100):  # Send 100 at a time to action batch function
        actions = actions_lst[i:i+100]
        batch_objects(base_url, api_key, org_id, actions)
        batch += 1

    print(f'Policy Objects ADDED to Dashboard: {count}')
    print(f'Action batches ADDED processed: {batch}')
    return


# Function to execute action batch
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
        print(f'Action Batch response status : {response.reason}')
        if response.reason == 'Bad Request':
            print(payload)
        print(f'Action Batch response code: {response.status_code}')  # We want a Status code of 201

    except HTTPError as http_err:
        print(f'An HTTP error has occured {http_err}')
    except Exception as err:
        print(f'An error has occured {err}')
    return


# Function to list policy objects in Dashboard
def list_network_obj(api_key, org_id):
    url = f'{base_url}/organizations/{org_id}/policyObjects/'

    try:
        payload = {}
        headers = {
            'X-Cisco-Meraki-API-Key': api_key,
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, data=payload)
        print(f'List Network Object response code: {response.status_code}')  # We want a Status code of 200

        json_obj_networks = json.loads(response.text)
        return json_obj_networks

    except HTTPError as http_err:
        print(f'An HTTP error has occured {http_err}')
    except Exception as err:
        print(f'An error has occured {err}')

    return


# Function to link policy objects to group objects in Dashboard
def link_objects_to_groups(api_key, org_id, linking_dict):
    network_obj_lst = []
    group_policy_obj_lst = []
    policy_obj_group_id = ''

    network_objects = list_network_obj(api_key, org_id)  # This will return a list

    # Create list of existing object names from the list of dictionaries
    for net_object in network_objects:
        name = net_object['name']
        id = net_object['id']
        policy_object = {
            'name': name,
            'id': id
        }
        network_obj_lst.append(policy_object)

    group_policy_objects = list_group_obj(api_key, org_id)

    # Create list of existing object names from the list of dictionaries
    for grp_object in group_policy_objects:
        name = grp_object['name']
        id = grp_object['id']
        group_policy_object = {
            'name': name,
            'id': id
        }
        group_policy_obj_lst.append(group_policy_object)  # Contains group policy name and id

    actions_lst = []
    obj_id_list = []
    count = 0
    batch = 0

    for group_object_name, networks in linking_dict.items():  # For group(key), networks(value) in linking dict
        obj_id_list.clear()  # Clear out list for next set
        val_count = len(networks)
        # Loop over networks list
        if val_count > 150:
            print(f'Number of policy objects for group {group_object_name} exceeds 150 Value Count is {val_count}')
            print(f'Please create additional group(s) for {group_object_name} for policies that exceed the 150 count limit.')
        else:

            for group_object in group_policy_obj_lst:
                group_name = group_object['name']
                group_id = group_object['id']
                if group_object_name == group_name:
                    policy_obj_group_id = group_id

            for net_name in networks:  # for net_name in networks
                for network_object in network_obj_lst:
                    name = network_object['name']
                    id = network_object['id']
                    if net_name == name:
                        obj_id_list.append(id)

            action_payload = {
                'resource': f'/organizations/{org_id}/policyObjects/groups/{policy_obj_group_id}',
                'operation': 'update',
                'body': {
                    'name': group_object_name,
                    'objectIds': obj_id_list
                    }
                }
            # A deep copy creates a *new object* and adds *copies* of nested objects in the original
            action_payload_copy = copy.deepcopy(action_payload)
            actions_lst.append(action_payload_copy)
            count += 1

    for i in range(0, len(actions_lst), 100):  # Send 100 at a time to action batch function
        actions = actions_lst[i:i+100]
        time.sleep(2)
        batch_objects(base_url, api_key, org_id, actions)
        batch += 1

    print(f'Policy Objects LINKED to Dashboard: {count}')
    print(f'Action batches LINKED processed: {batch}')


def main():
    csv_file, api_key, org_id = collect_info()
    read_csv(csv_file, api_key, org_id)


if __name__ == '__main__':
    main()
