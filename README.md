
# Meraki Policy Objects

These scripts are for **demonstration and education** purposes. They are **not** intended to be run in a production network. 

## Introduction

At the time of this writing Meraki Network Objects is an Open Beta feature and the recommendation is to first test this feature in an isolated lab environment before moving to production.

Details can be found here on how to enable the Open Beta Network Objects:

 [Network Objects Configuration Guide](https://documentation.meraki.com/MX/Firewall_and_Traffic_Shaping/Network_Objects_Configuration_Guide)


## Description

The purpose of these scripts is to demonstrate how to use Meraki Policy Object APIs to create Policy Object Groups and Policy Objects and then place the proper Policy Object in the appropriate group. 

Policy Object Group and Policy Object information will come from a .csv file called **object-import.csv** that will be read in by the script **create_policy_objects.py** .

There is a potential for the number of objects in the .csv file to be quite numerous, so Action Batches will be leveraged to speed up the configuration process. 

A second script exists to leverage the newly created Policy Groups and Policy object to create L3 Firewall rules. The rules will come from a .csv file called **fw-rules.csv** that will be read in to script **create_l3_fw_rules.py** .


## Installation / How to run the scripts

It is recommended to run these scripts inside of a Virtual Environment. 

For information on creating and activating a virtual enviroment please see: 

[Python Packaging User Guide: Creating and using virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)


NOTE : README not yet complete


