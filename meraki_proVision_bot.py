from meraki.meraki import Meraki
from meraki.models.create_organization_networks_model import (
   CreateOrganizationNetworksModel 
)
from meraki.models.claim_network_devices_model import (
    ClaimNetworkDevicesModel
)
import pytesseract
import requests
import io
import sys
from PIL import Image
from PIL import ImageFilter
import re
from flask import Flask
from flask import request, redirect
from webexteamssdk import WebexTeamsAPI
import sys, getopt
import json
from pprint import pprint

FLOW = ""
STEP = 0
RESPONSE = ""

# Configuration parameters and credentials for MERAKI
x_cisco_meraki_api_key = 'MERAKI API KEY'

client = Meraki(x_cisco_meraki_api_key)

# Configuration and parametes for WEBEX TEAMS
access_token="WEBEX TEAMS BOT ACCESS TOKEN"
teamsapi = WebexTeamsAPI(access_token=access_token)
botid = "BOT ID->get this from the /me call using the bots access token...the id generated when creating the bot is NOT the right id"
ROOM_ID = ""

app = Flask(__name__)


@app.route('/handler', methods=['POST'])
def message_handler():
    global ROOM_ID
    #print(request.data)
    message_data = json.loads(request.data)
    ROOM_ID = message_data["data"]["roomId"]
    person_id = message_data["data"]["personId"]
    if person_id != botid:
        message = teamsapi.messages.get(message_data["data"]["id"])
        message_parser(message)
    
        
    return "message received"

def message_parser(message):
    global FLOW
    global STEP
    global RESPONSE
    global ROOM_ID

    if message.text != None:
        message = message.text

    print(message)
    if FLOW == "" and STEP == 0:
        message_match = message.lower()
        if message_match.find("help") > -1 or message_match.find("hi") > -1:
            response = "Hi there! I'm the Meraki ProVision Bot!  \n\n" \
                + "I can do the following \n\n" \
                + "* New - Create a Provision a new network and add devices \n" \
                + "* Add - Add a device to an existing network\n" \
                + "* Remove - Remove a device from a network\n" \
                + "* Delete - Delete a network\n"
            teamsapi.messages.create(ROOM_ID, markdown=response)
        elif message_match.find("new") > -1 or \
                message_match.find("add") > -1 or \
                message_match.find("remove") > -1 or \
                message_match.find("delete") > -1:
            list_orgs()
            FLOW = message_match
            STEP += 1
        '''
        elif message.find("add"):
            add_device_flow()
        elif message.find("remove"):
            remove_device_flow()
        elif message.find("delete"):
            delete_device_flow()
        '''
    elif FLOW == "new":
        if STEP == 1:
            select_org(message)
            STEP += 1
        elif STEP == 2: 
            create_new_network(message)
            STEP += 1
        elif STEP == 3:
            hasMR = provision_devices(message)
            '''if hasMR:
                STEP +=1
            else:'''
            STEP = 0
            FLOW = ""
    '''
        elif STEP == 4:
            update_ssid(message)
            STEP = 0
            FLOW = ""
    elif FLOW == "add":
        if STEP == 1:
            select_org(message)
            STEP += 1
        elif STEP == 2: 
            select_network(message)
            STEP += 1
        elif STEP == 3:
            hasMR = provision_devices(message)
            if hasMR:
                STEP +=1
            else:
                STEP = 0
                FLOW = ""
        elif STEP == 4:
            update_ssid(message)
            STEP = 0
            FLOW = ""
    elif FLOW == "remove":
        if STEP == 1:
            select_org(message)
            STEP += 1
        elif STEP == 2: 
            select_network(message)
            STEP += 1
        elif STEP == 3:
            remove_devices(message)
            STEP = 0
            FLOW = ""
    elif FLOW == "delete":
        if STEP == 1:
            select_org(message)
            STEP += 1
        elif STEP == 2: 
            select_network(message)
            remove_devices(message)
            delete_network(message)
            STEP = 0
            FLOW = ""
    '''


def list_orgs():
    global FLOW
    global STEP
    global RESPONSE
    orgs = ""
    try:
        orgs = client.organizations.get_organizations()
        response = "Here are your list of organizations. " \
            + "Select the one you'd like to administer by entering it's number \n"
        for index, org in enumerate(orgs, start=1):
            response = response \
             + str(index) + ". " + org["name"] + " - " + str(org["id"]) + "\n"
        teamsapi.messages.create(ROOM_ID, markdown=response)
        RESPONSE = orgs
    except Exception as e:
        pprint(e)

def select_org(message):
    global FLOW
    global STEP
    global RESPONSE

    for index, org in enumerate(RESPONSE, start=1):
        if index == int(message):
            RESPONSE = org["id"]
            pprint("User chose org " + str(RESPONSE))
            teamsapi.messages.create(ROOM_ID, text="Wonderful! Now type in the name of this new network")
    

def create_new_network(message):
    global FLOW
    global STEP
    global RESPONSE

    try:
        collect = {}
        organization_id = RESPONSE
        collect['organization_id'] = organization_id

        create_organization_networks = CreateOrganizationNetworksModel()
        create_organization_networks.name = message
        create_organization_networks.mtype = 'appliance switch camera wireless'
        create_organization_networks.tags = ''
        create_organization_networks.time_zone = 'America/Los_Angeles'
        create_organization_networks.disable_my_meraki_com = False
        collect['create_organization_networks'] = create_organization_networks

        RESPONSE = client.networks.create_organization_networks(collect)
        RESPONSE = RESPONSE["id"]
        teamsapi.messages.create(ROOM_ID, text="GREAT NAME! Network with ID:  " \
            + RESPONSE + " created")
        teamsapi.messages.create(ROOM_ID, text="Now upload pictures of the placards of the devices you'd like to provision to this network")
    except Exception as e:
        pprint(e)

def provision_devices(message):
    global FLOW
    global STEP
    global RESPONSE

    collect = {}
    network_id = RESPONSE
    collect['network_id'] = network_id

    files = message.files
    try:
        for file in files:
            claim_network_devices = ClaimNetworkDevicesModel()
            claim_network_devices.serial = find_serial(file)
            collect['claim_network_devices'] = claim_network_devices

            result = client.devices.claim_network_devices(collect)
            teamsapi.messages.create(ROOM_ID, text="Device with serial " \
                + claim_network_devices.serial \
                + " added to network")
        return True  
    except Exception as e:
        pprint(e)
        return False


def find_serial(file):
    headers={'Authorization':'Bearer ' + access_token}
    image = Image.open(requests.get(file, headers=headers, stream=True).raw) 
    print(image)
    #print("The raw output from tesseract with no processing is:\n\n")
    print("-----------------BEGIN-----------------")
    image_string = pytesseract.image_to_string(image)
    image_string = image_string.replace(" ", "")
    print(image_string)
    search_strs = ['SN:', 'SN(N/S):']

    for search_str in search_strs:      
        if image_string.find(search_str) > -1:
            print('found!')
            start = image_string.find(search_str)
            end = start + len(search_str) + 14
            serial = image_string[start + len(search_str):end]
            print(serial)
            return serial
    
    return "Serial NOT FOUND!"
    

def main(argv):
    url=""
    try:
        opts, args = getopt.getopt(argv, "hu:", ["url="])
    except getopt.GetoptError:
        print("meraki_proVision_bot.py -u <url>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("meraki_proVision_bot.py -u <url>")
            sys.exit()
        elif opt in ("-u", "--url"):
            url = arg

    print("application url: " + url)
    return url


if __name__ == "__main__":
    url = main(sys.argv[1:])
    #teamsapi.webhooks.create("merakiproVisionbot", url+"/handler", "messages", "created")


    app.run(host="0.0.0.0", port=5005,threaded=True,debug=False)
