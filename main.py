
import requests
import json


def collect_info():
    api_key = input('Enter your Meraki Dashboard API Key: ')
    return api_key


def main():
    api_key = collect_info()
    print(api_key)


if __name__ == "__main__":
    main()