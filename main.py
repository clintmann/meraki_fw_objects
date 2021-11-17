
import requests
from requests.models import HTTPError
import meraki
import getpass
import csv
import json


obj_name_lst = []
obj_group_lst = []
obj_dict = {}
obj_dict_lst = []
linking_dict = {}
linking_dict_lst = []
extisting_group_obj_lst = []
extisting_net_obj_lst = []
network_obj_lst = []
obj_id_list = []
group_policy_obj_lst = []
base_url = "https://api.meraki.com/api/v1"
csv_file = "Meraki_Import_test.csv"


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
            #print(f"Organization ID: {org_id}")
        else:
            raise ValueError('The organization name does not exist')

    return org_id


def read_csv(csv_file, api_key, org_id):
    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                obj_name = row['name']
                obj_category = row['category']
                obj_type = row['type']
                obj_cidr = row['cidr']
                obj_grp_name = row['Group Name']

                # Create "linking" dictionary
                # This contains the object name and group it belongs to
                # If there is no key with the Object Group Name create one
                if obj_grp_name not in linking_dict:
                    linking_dict[obj_grp_name] = list()
                    linking_dict[obj_grp_name].append(obj_name)
                else:
                    # Key exists check if object is in the list of values
                    if obj_name in linking_dict[obj_grp_name]:
                        print(f"Object {obj_name} already exists in Group {obj_grp_name}")
                    else:
                        # Key exists add object not in list of values - add it
                        linking_dict[obj_grp_name].append(obj_name)

                # Create a list of unique Group Names
                # If the group is not in the list then add it
                if obj_grp_name not in obj_group_lst:
                    # append to list
                    obj_group_lst.append(obj_grp_name)
                else:
                    # Object name already exists
                    print(f"* Group {obj_grp_name} already exists in group object list.")

                # Create a list of unique Network Object Names
                # If object is not in the list then add it
                if obj_name not in obj_name_lst:
                    # append to list
                    obj_name_lst.append(obj_name)

                # Create a dictionary with key value pairs of
                # Name, Category, Type, CIDR
                # Then append the dictionary to obj_dict_lst list
                # This will be the Body of the API call
                    obj_dict = {
                                "name": obj_name,
                                "category": obj_category,
                                "type": obj_type,
                                "cidr": obj_cidr,
                                "groupIds": []
                                }
                    obj_dict_lst.append(obj_dict)
                else:
                    # Object name already exists
                    print(f"* Network Object name {obj_name} already exists in network object list.")

            # Call function: to determine if group object exists or needs created
            check_group_obj(api_key, obj_group_lst, org_id)

            # Call function: to determine if network object exists or needs created
            check_net_obj(api_key, obj_name_lst, obj_dict_lst, org_id)

            # Call function: to link network objects to group objects
            link_obj_groups(api_key, org_id, linking_dict)

            # Count number of Dictionaries in List
            # obj_count = len(obj_dict_lst)
            # print(f"Object Count: {obj_count}")

    except IOError:
        print("I/O error")

    return


def check_group_obj(api_key, obj_group_lst, org_id):
    # Check if the group object already exists using List Group function
    existing_group_obj = list_group_obj(api_key, org_id)  # this will return a list

    # Create list of existing object names from the list of dictionaries
    for i in existing_group_obj:
        name = i['name']
        if name not in existing_group_obj:
            # append to list
            extisting_group_obj_lst.append(name)

    # Search list of dictionaries to see if group object name exists
    # Create Object Group for each item in obj_group_lst
    for group in obj_group_lst:
        if existing_group_obj:   # list is not empty - some group objects found in Dashboard
            print("Existing Group Object list NOT empty")
            # Create Object Group for each item in obj_group_lst
            if group in extisting_group_obj_lst:
                print(f"Group {group} is already configured in Dashboard.")
            else:
                print("Need to create group object")
                # Call Function to make API Call
                create_group_post(api_key, org_id, group)

        else:   # list is empty - no network objects found in Dashboard
            print("Existing Group Object list EMPTY - create group object(s)")

                # Call Function to make API Call
            create_group_post(api_key, org_id, group)
    return


def create_group_post(api_key, org_id, group):
    url = f"{base_url}/organizations/{org_id}/policyObjects/groups"

    try:
        payload = json.dumps({
                              "name": group,
                              "objectIds": []
                            })
        headers = {
                   'X-Cisco-Meraki-API-Key': api_key,
                   'Content-Type': 'application/json'
                  }

        response = requests.post(url, headers=headers, data=payload)
        print(f"Create Group response code {response.status_code}")  # We want a Status code of 201

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")

    return


def list_group_obj(api_key, org_id):
    url = f"{base_url}/organizations/{org_id}/policyObjects/groups"

    try:
        payload = {}
        headers = {
                    'X-Cisco-Meraki-API-Key': api_key,
                    'Content-Type': 'application/json'
                  }

        response = requests.get(url, headers=headers, data=payload)
        print(f"List Group response code: {response.status_code}")  # We want a Status code of 200

        json_obj_groups = json.loads(response.text)

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")

    return json_obj_groups


def update_group_obj(api_key, org_id, policy_obj_group_id, payload_body):
    url = f"{base_url}/organizations/{org_id}/policyObjects/groups/{policy_obj_group_id}"

    try:
        payload = json.dumps(payload_body)
        headers = {
                    'X-Cisco-Meraki-API-Key': api_key,
                    'Content-Type': 'application/json'
                  }

        response = requests.put(url, headers=headers, data=payload)
        print(f"Update Group response code: {response.status_code}")  # We want a Status code of 201

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")

    return


def check_net_obj(api_key, obj_name_lst, obj_dict_lst, org_id):
    # **** this needs checked - for when dashboard is empty
    # Check if the group object already exists using List Network Object function
    existing_net_obj = list_network_obj(api_key, org_id)  # this will return a list of dictionaries

    # Create list of existing object names from the list of dictionaries
    for i in existing_net_obj:
        name = i['name']
        if name not in existing_net_obj:
            # append to list
            extisting_net_obj_lst.append(name)

    # Search list of dictionaries to see if network object name exists
    # Create Network Object for each item in obj_net_lst

    for network in obj_name_lst:
        if existing_net_obj:   # list is not empty - network objects found in Dashboard
            print("Existing Network Object list NOT empty")

            if network in extisting_net_obj_lst:
                print(f"Network {network} is already configured in Dashboard.")
            else:
                print("Need to create network object")
                # Call Function to make API Call
                # if network in obj_dict_list
                for d in obj_dict_lst:   # choose item in obj_dict_lst
                    if network == d['name']:
                        print("Network equal dName")
                        payload_body = {
                                            "name": d['name'],
                                            "category": d['category'],
                                            "type": d['type'],
                                            "cidr": d['cidr'],
                                            "groupIds": []
                                           }
                        create_net_obj_post(api_key, org_id, payload_body)

        else:   # list is empty - no network objects found in Dashboard
            for d in obj_dict_lst:
                if network == d['name']:
                    # print(f"this is d: {d}")
                    payload_body = {
                                    "name": d['name'],
                                    "category": d['category'],
                                    "type": d['type'],
                                    "cidr": d['cidr'],
                                    "groupIds": []
                                   }
                
                    create_net_obj_post(api_key, org_id, payload_body)

    return


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

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")

    return json_obj_networks


def create_net_obj_post(api_key, org_id, payload_body):
    url = f"{base_url}/organizations/{org_id}/policyObjects/"

    try:
        payload = json.dumps(payload_body)
        headers = {
                   'X-Cisco-Meraki-API-Key': api_key,
                   'Content-Type': 'application/json'
                  }

        response = requests.post(url, headers=headers, data=payload)
        print(f"Create Network Object response code {response.status_code}")  # We want a Status code of 201

    except HTTPError as http_err:
        print(f"An HTTP error has occured {http_err}")
    except Exception as err:
        print(f"An error has occured {err}")

    return


def link_obj_groups(api_key, org_id, linking_dict):
    policy_obj_group_id = ""
    network_objects = list_network_obj(api_key, org_id)  # this will return a list

    # Create list of existing object names from the list of dictionaries
    for n in network_objects:
        name = n['name']
        id = n['id']
        network_obj_dict = {
                                "name": name,
                                "id": id
                           }
        network_obj_lst.append(network_obj_dict)

    group_policy_objects = list_group_obj(api_key, org_id)

    # Create list of existing object names from the list of dictionaries
    for p in group_policy_objects:
        name = p['name']
        id = p['id']
        group_policy_obj_dict = {
                                "name": name,
                                "id": id
                           }
        group_policy_obj_lst.append(group_policy_obj_dict) # contains group policy name and id

    # TESTING/VALIDATION linking dictionary
    for key, value in linking_dict.items():
        obj_id_list.clear()  # clear out list for next set
        # print(key, ' : ', value)
        val_count = len(value)
        print(f"Number of policy objects for group {key}: {val_count}")
        # loop over value list
        for policy in value:
            for d in network_obj_lst:
                name = d['name']
                id = d['id']
                if policy == name:
                    obj_id_list.append(id)

        for g in group_policy_obj_lst:
            gname = g['name']
            gid = g['id']
            if key == gname:
                policy_obj_group_id = gid

        payload_body = {"name": key,
                        "objectIds": obj_id_list
                        }

        update_group_obj(api_key, org_id, policy_obj_group_id, payload_body)


def main():
    api_key, dashboard, org_id = collect_info()
    read_csv(csv_file, api_key, org_id)


if __name__ == "__main__":
    main()
