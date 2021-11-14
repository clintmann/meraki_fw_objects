
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


def read_csv(api_key, org_id):
    try:
        with open('Meraki_Import_test.csv', newline='', encoding='utf-8-sig') as csvfile:
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
                    print(f"Linking Dictionary: {linking_dict}")
                    linking_dict[obj_grp_name].append(obj_name)
                else:
                    # Key exists check if object is in the list of values
                    if obj_name in linking_dict[obj_grp_name]:
                        print(f"Object {obj_name} already exist in Group {obj_grp_name}")
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
                    print(f"Group {obj_grp_name} already exists.")

                # Create a list of unique Object Names
                # If object is not in the list then add it
                if obj_name not in obj_name_lst:
                    # append to list
                    obj_name_lst.append(obj_name)

                # Create a dictionary with key value pairs of
                # Name, Category, Type, CIDR
                # Then append the dictionary to obj_dict_lst list
                # This will be the Body of the API call
                    obj_dict = {
                                'name': obj_name,
                                'category': obj_category,
                                'type': obj_type,
                                'cidr': obj_cidr,
                                'groupIds': []
                                }
                    obj_dict_lst.append(obj_dict)
                else:
                    # Object name already exists
                    print(f"Object name {obj_name} already exists.")            

            # Call function: to determine if group object exists or needs created
            check_group_obj(api_key, obj_group_lst, org_id)

            # Call function: to determine if network object exists or needs created
            check_net_obj(api_key, obj_name_lst, org_id)

            #print(f"List of Object Name and Group Link {linking_dict_lst}")
            #print(f"List of Object Dictionaries {obj_dict_lst}")
            
            # Count number of Dictionaries in List
            # Using list comprehension + isinstance()
            #obj_count = len([ele for ele in obj_dict_lst if isinstance(ele, dict)])
            obj_count = len(obj_dict_lst)
            print(f"Object Count: {obj_count}")
            '''
            # TESTING/VALIDATION Print linking dictionary
            for key, value in linking_dict.items():
                print(key, ' : ', value)
            '''
            #grp_name = row['Group Name']
            #print(f"Object Name: {grp_name}")
            
            # Add to list
            # If group is not in the list then add it

            # Once data is imported
            # Call link function to add objects to correct group
            # 150 object limit per group

        # TESTING/VALIDATION - Iterate over key/value pairs in dict and print them
        # for key, value in obj_dict.items():
        #    print(key, ' : ', value)

    except IOError:
        print("I/O error")


def check_group_obj(api_key, obj_group_lst, org_id):
    #url = f"{base_url}/organizations/{org_id}/policyObjects/groups"

    # Check if the group object already exists using List Group function
    existing_group_obj = list_group_obj(api_key, org_id)
    # print(f"Existing Object Groups: {existing_group_obj}")
    # print(type(existing_group_obj))
    # Search list of dictionaries to see if group object name exists
    # Create Object Group for each item in obj_group_lst
    print(f"Object Group List: {obj_group_lst}")
    for group in obj_group_lst:
        # Search list of dictionaries to see if group object name exists
        for i in existing_group_obj:
            #name = i['name']
            #print(f"Existing Object: {name} Group to Add?: {group}")
            if i['name'] in obj_group_lst:
                print(f"Group {group} is already configured in Dashboard.")
            elif group not in obj_group_lst and group not in existing_group_obj:
                print("Need to create group")
                # Call Function to make API Call
                create_group_post(api_key, org_id, group)


def check_net_obj(api_key, obj_name_lst, org_id):
    #url = f"{base_url}/organizations/{org_id}/policyObjects/groups"

    # Check if the group object already exists using List Network Object function
    existing_net_obj = list_group_obj(api_key, org_id)
    # print(f"Existing Object Groups: {existing_group_obj}")
    # print(type(existing_net_obj))
    # Search list of dictionaries to see if network object name exists
    # Create Object Group for each item in obj_net_lst
    print(f"Object Network List: {obj_name_lst}")
    for group in obj_group_lst:
        # Search list of dictionaries to see if group object name exists
        for i in existing_net_obj:
            #name = i['name']
            #print(f"Existing Object: {name} Group to Add?: {group}")
            if i['name'] in obj_name_lst:
                print(f"Group {group} is already configured in Dashboard.")
            elif group not in obj_name_lst and group not in existing_net_obj:
                print("Need to create group")
                # Call Function to make API Call
                create_net_obj_post(api_key, org_id, group)


def create_group_post(api_key, org_id, group):
    url = f"{base_url}/organizations/{org_id}/policyObjects/groups"

    try:
        print("try")
        payload = json.dumps({
                              'name': group,
                              'objectIds': []
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
    # print("List group object function")
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

    '''
    Lists Policy Object Groups belonging to the organization.
     HTTP REQUEST
     GET/organizations/{organizationId}/policyObjects/groups
    '''
    return json_obj_groups


def update_group_obj(org_id):
    url = f"{base_url}/organizations/{org_id}/policyObjects/groups/{policyObjectGroupId}"
    '''
     Updates a Policy Object Group.
     HTTP REQUEST
     PUT/organizations/{organizationId}/policyObjects/groups/{policyObjectGroupId}
    '''


def create_net_obj_post(obj_dict_lst):
    print(f"Network Object Dictionary List: {obj_dict_lst}")


def main():
    api_key, dashboard, org_id = collect_info()
    read_csv(api_key, org_id)


if __name__ == "__main__":
    main()
