#
# This script is for demonstation purposes only.
# It uses Meraki APIs to apply Network Objects/Groups
# to layer 3 firewall rules.
#
# This script is used after create_policy_objects.py
#
# The script will import information from a .csv file.
# There is an sample template called fw-rules.csv
#

import os.path
import requests
from requests.models import HTTPError
import getpass
import csv
import json
import copy


base_url = 'https://api.meraki.com/api/v1'


# List the organizations that the user has access to
def get_user_orgs(api_key):
    get_url = f'{base_url}/organizations'
    headers = {'X-Cisco-Meraki-API-Key': api_key,
               'Content-Type': 'application/json'
               }

    response = requests.get(get_url, headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


def get_networks(api_key, org_id):
    get_url = f'{base_url}/organizations/{org_id}/networks'
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
    print('It will use Meraki APIs to apply')
    print('Network Objects/Groups to layer 3 firewall rules\n')
    print('********************DEMO********************\n')

    while True:
        csv_file = input("Please enter the name of the .csv file containing the firewall rules: ")
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
    print('You have access to these organizations with that API key.')
    print('Organization ID\t\tOrganization Name'.expandtabs(8))
    for org in orgs:
        org_id = org['id']
        org_name = org['name']
        org_ids.append(str(org_id))
        org_names.append(org_name)

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

    while True:
        (ok, nets) = get_networks(api_key, org_id)
        if ok:
            break
        else:
            print('There was a problem retrieving the networks.\n')

    net_ids = []
    net_names = []
    print('You have access to these networks in that organization.')
    print('Network Name\t\tNetwork ID'.expandtabs(8))

    for net in nets:
        net_id = net['id']
        net_name = net['name']
        net_ids.append(str(net_id))
        net_names.append(net_name)
        networks = {net_names[i]: net_ids[i] for i in range(len(net_names))}
        print(f'{net_name:20}\t{net_id}')
    print()

    while True:
        # Ask for network ID
        net_name = input('Please enter the Network Name you would like to configure: ')

        if net_name in networks.keys():
            net_id = networks.get(net_name)
            print(f"Adding Firewall rules to:\n\tNetwork Name - {net_name}\n\tNetwork ID   - {net_id}")
            print()
            break
        else:
            print('That Network Name is not one listed, try another.\n')

    return csv_file, api_key, org_id, net_id


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


# Function to read csv file
def read_csv(api_key, net_id, csv_file, group_obj_lst, network_obj_lst):
    src_cidr_lst = []
    src_port_lst = []
    dest_cidr_lst = []
    dest_port_lst = []
    row_values = []
    fw_rule_payload = {}
    dest_cidr_group_id_lst = []
    dest_cidr_network_id_lst = []
    src_cidr_group_id_lst = []
    src_cidr_network_id_lst = []
    fw_rule_dict = {}
    fw_rule_lst = []

    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            # The data from four columns in the file will be used
            # The columns are name, category, type, cidr and Group Name
            # Read in data from the relevant columns in the row
            # and assign it to a variable
            rule = 0
            # Read in row
            for row in reader:
                row_values = list(row.values())
                # Check if row is empty
                result = all(element == row_values[0] for element in row_values) # Will be True if all values are the same
                if not result:  # Row is not empty
                    rule_number = row['Rule Number']
                    policy = row['Policy']
                    comment = row['Comment']
                    protocol = row['Protocol']
                    src_cidr = row['Source CIDR']
                    src_port = row['Source Port']
                    dest_cidr = row['Destination CIDR']
                    dest_port = row['Destination Port']
                    syslog = row['Syslog Enabled']
                    if rule_number:  # Rule number field not empty
                        if rule_number == 'END':
                            break
                        elif int(rule_number) > rule:
                            rule_policy = policy.strip() # Strip away white spaces
                            rule_comment = comment
                            rule_protocol = protocol.strip()
                            rule_syslog = syslog

                            if src_cidr:
                                src_cidr_lst.append(src_cidr.strip())
                            if src_port:
                                src_port_lst.append(src_port.strip())
                            if dest_cidr:
                                dest_cidr_lst.append(dest_cidr.strip())
                            if dest_port:
                                dest_port_lst.append(dest_port.strip())
                            rule = int(rule_number)
                    else:   # Rule number field is empty - same rule more info
                        if src_cidr:
                            src_cidr_lst.append(src_cidr.strip())
                        if src_port:
                            src_port_lst.append(src_port.strip())
                        if dest_cidr:
                            dest_cidr_lst.append(dest_cidr.strip())
                        if dest_port:
                            dest_port_lst.append(dest_port.strip())

                else:  # Row empty
                    # Determine if destinatino is a group or network object
                    for dest in dest_cidr_lst:
                        if dest == 'Any':
                            dest_cidr_group_id_lst.append(dest)
                            break
                        # Is dest a group?
                        for grp_object in group_obj_lst:
                            if dest in grp_object.values():
                                name = grp_object['name']
                                id = grp_object['id']
                                print(f'DEST NAME: {name} {id}')
                                dest_cidr_group_id_lst.append(f'GRP({id})')  # Contains group policy name and id
                                break
                    list_len = len(dest_cidr_group_id_lst)

                    if list_len > 0:
                        exist_as_group_object = True
                    else:
                        exist_as_group_object = False

                    if exist_as_group_object is False:  # Destination is not a group check network objects to find it
                        for dest in dest_cidr_lst:
                            # Check if the dest ends in /32 if so, remove the /32
                            if dest.endswith('/32'):  # item is an IP address
                                dest = dest.replace('/32', '')
                                for net_object in network_obj_lst:
                                    if dest in net_object.values():
                                        net_cidr = net_object['cidr']
                                        id = net_object['id']
                                        print(f'NAME: {net_cidr} {id}')
                                        dest_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                        break
                            else:  # item is a policy object name
                                for net_object in network_obj_lst:
                                    if dest in net_object.values():
                                        net_name = net_object['name']
                                        id = net_object['id']
                                        print(f'NAME: {net_name} {id}')
                                        dest_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                        break
                    # Determine if source is a group or network object
                    for src in src_cidr_lst:
                        # Is source a group?
                        if src == 'Any':
                            src_cidr_group_id_lst.append(src)
                            break

                        for grp_object in group_obj_lst:
                            if src in grp_object.values():
                                name = grp_object['name']
                                id = grp_object['id']
                                print(f'Source NAME: {name} {id}')
                                src_cidr_group_id_lst.append(f'GRP({id})')  # Contains group policy name and id
                                break
                    # Check if there are items in the group list by checking length
                    list_len = len(src_cidr_group_id_lst)
                    if list_len > 0:
                        exist_as_group_object = True
                    else:
                        exist_as_group_object = False

                    if exist_as_group_object is False:  # Destination is not a group check network objects to find it
                        for src in src_cidr_lst:
                            # Check if the the source ends in /32 remove the /32
                            if src.endswith('/32'):  # item is an IP address
                                src = src.replace('/32', '')
                                print(f'Checking network source {src}')
                                for net_object in network_obj_lst:
                                    if src in net_object.values():
                                        net_cidr = net_object['cidr']
                                        id = net_object['id']
                                        print(f'NAME: {src} {net_cidr} {id}')
                                        src_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                        break
                            else:  # item is a policy object name
                                print(f'Checking network source {src}')
                                for net_object in network_obj_lst:
                                    if src in net_object.values():
                                        net_name = net_object['name']
                                        id = net_object['id']
                                        print(f'NAME: {src} {net_name} {id}')
                                        src_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                        break

                    # Change dest port from list to sting
                    dest_ports = ','.join(dest_port_lst)
                    # Change source port from list to string
                    src_ports = ','.join(src_port_lst)

                    # Create rule payload there could be objects from group list 
                    # and network list as src and destCidr

                    src_cidr_string = ''
                    dest_cidr_string = ''

                    # Join all the ids in the destination group id list and network id list
                    if len(dest_cidr_group_id_lst) > 0:
                        dest_cidr_string = ','.join(dest_cidr_group_id_lst)
                        print(dest_cidr_string)
                    if len(dest_cidr_network_id_lst) > 0:
                        dest_cidr_string = ','.join(dest_cidr_network_id_lst)
                    # Join all the ids in the source group id list and network id list
                    if len(src_cidr_group_id_lst) > 0:
                        src_cidr_string = ','.join(src_cidr_group_id_lst)
                    if len(src_cidr_network_id_lst) > 0:
                        src_cidr_string = ','.join(src_cidr_network_id_lst)

                    # Fill in parameters for firewall rule
                    fw_rule_dict = {
                        "comment": rule_comment,
                        "policy": rule_policy,
                        "protocol": rule_protocol,
                        "destPort": dest_ports,
                        "destCidr": dest_cidr_string,
                        "srcPort": src_ports,
                        "srcCidr": src_cidr_string,
                        "syslogEnabled": rule_syslog
                    }
                    # Create a list of firewall rules
                    fw_rule_dict_copy = copy.deepcopy(fw_rule_dict)
                    fw_rule_lst.append(fw_rule_dict_copy)

                    # Clear variables and lists for next loop
                    rule_policy = ''
                    rule_comment = ''
                    rule_protocol = ''
                    rule_syslog = ''

                    src_cidr_lst.clear()
                    src_port_lst.clear()
                    dest_cidr_lst.clear()
                    dest_port_lst.clear()
                    dest_cidr_group_id_lst.clear()
                    dest_cidr_network_id_lst.clear()
                    src_cidr_group_id_lst.clear()
                    src_cidr_network_id_lst.clear()

            # Generate payload
            for d in fw_rule_lst:
                fw_rule_payload = json.dumps({
                    "rules":
                        fw_rule_lst
                })

            # Call function to create firewall rules
            create_fw_rules(api_key, base_url, net_id, fw_rule_payload)

    except IOError:
        print('I/O error')

    return


# Function to make API call to create firewall rules
def create_fw_rules(api_key, base_url, net_id, fw_rule_payload):
    url = f'{base_url}/networks/{net_id}/appliance/firewall/l3FirewallRules'

    try:
        payload = fw_rule_payload

        headers = {
          'X-Cisco-Meraki-API-Key': api_key,
          'Content-Type': 'application/json'
        }

        response = requests.request("PUT", url, headers=headers, data=payload)
        print(f'Create Firewall Rules response status : {response.reason}')
        print(f'Create Firewall Rules response code: {response.status_code}')  # We want a Status code of 200
        print(response.text)

    except HTTPError as http_err:
        print(f'An HTTP error has occured {http_err}')
    except Exception as err:
        print(f'An error has occured {err}')
    return


def main():
    group_obj_lst = []
    network_obj_lst = []
    csv_file, api_key, org_id, net_id = collect_info()
    group_obj_lst = list_group_obj(api_key, org_id)
    network_obj_lst = list_network_obj(api_key, org_id)
    #print(group_obj_lst)
    #print(type(group_obj_lst))
    read_csv(api_key, net_id, csv_file, group_obj_lst, network_obj_lst)


if __name__ == '__main__':
    main()
