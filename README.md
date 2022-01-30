
# Create Meraki Firewall Rules Using Policy Objects


These scripts are intended for **DEMONSTRATION and EDUCATION** purposes. They are **NOT** meant to be run in a production network. 


## Introduction

At the time of this writing Meraki Network Objects is an Open Beta feature and the recommendation is to first test this feature in an isolated lab environment before moving to production.

Details can be found here on how to enable the Open Beta Network Objects:

 [Network Objects Configuration Guide](https://documentation.meraki.com/MX/Firewall_and_Traffic_Shaping/Network_Objects_Configuration_Guide)

Meraki API documentation is here: https://developer.cisco.com/meraki/


## Description

The purpose of these scripts is to demonstrate how to use RESTful APIs to programmatically 
- Create Policy Objects 
- Create Policy Object Groups
- Add Policy Objects to the appropriate Policy Object Groups
- Leverage the Policy Objects and Policy Object Groups to create Layer 3 or Site-to-Site VPN firewall rules

## Getting Started

1. Create a .csv file that contains your Policy Objects and Policy Object Groups. Use the  **sample-object-import.csv** as a template.

The first row of the .csv must contain the following column headers

**name | category | type | cidr | fqdn | groupName**

These are the PARAMETERS that will be used for our API Request Body. 

DETAILS: 
- The NAME of a policy objects and policy object groups must be alphanumeric. They can contain   spaces, dashes, or underscore characters and must be unique within the organization. A period (.) or foward slash (/) in the name will not be accepted. Take this into account when naming your subnets.

- The CATEGORY field will always be *network* in our use case.

- The TYPE field will either be cidr or fqdn
- If the policy object is not part of a policy object group. Leave the groupName field empty.
- If the policy object is in multiple policy object groups; enter the object name, category, type cidr or fqnd in a new row with the second groupName. 
- Policy object groups can only contain 150 objects. Therefore, you may have to break up some of your groups in order to adhere to the 150 object limit.


2. Create a .csv file that contains either your Layer 3 or site-to-site VPN firewall rules. Use the use the  **sample-fw-rules.csv** as a template.

The first row of the .csv must contain the following column headers

**Rule Number | Policy | Comment | Protocol | Source CIDR | Source Port | Destination CIDR | Destination Port | Syslog Enabled**

There must be an empty row between each firewall rule. 
The last firwall rule will be followed by a row with each the word **END** in each field as shown in the **sample-fw-rules.csv** template.

DETAILS: 
- Firewall rules can have one port range defined (5000-7500) or a group of individual ports (80,443,558) but not both. They also can’t have 2 ranges (5000-7500, 10000-11000). If multiple port ranges are required. Each range must be in a new row.
- Meraki rules can be created for the following protocls: TCP, UDP, ICMP, or ANY. Unless you use ANY, you can’t define TCP and UDP in the same rule. If you require both TCP and UDP, you can create two separate rules. One for TCP and one for UDP. 



## Installation

It is recommended to run these scripts inside of a Virtual Environment. 

For information on creating and activating a virtual enviroment please see: 

[Python Packaging User Guide: Creating and using virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)

1. Clone repository
2. Run the *create_policy_objects.py* script to policy objects and policy object groups
3. Run the *create_fw_rules.py* script. You will prompted you to create either layer 3 firewall or site-to-site vpn rules.  

DETAILS:
- The policy objects and groups will append anything new without touching the existing objects/groups. After the first import, you can use smaller files with just a few new items to add new objects/groups or to adjust the group membership of an existing object.
 
- The Firewall rules will always overwrite the existing rules with whatever is in the import file. This is a function of how the API call works. If you want to add a rule, you should add it to the .csv file and re-run the *create_fw_rules.py* script

