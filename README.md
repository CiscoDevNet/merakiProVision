# merakiProVision
merakiProVision is a Python based WebEx Teams bot that can provision Meraki network devices by uploading pictures of the device placards.


## Caveats
This is a single-threaded Flask application for demo/sample-code purposes.  Running this as-is locally and using a reverse-proxy tool like [ngrok](https://ngrok.com) will only allow for a single bot interaction at a time and multiple interactions at one time could result in confusing results.

When sending pictures, for best results make sure they are right side up and the serial number of the Meraki device is clear.

## Requirements:

1. Installation of [Tesseract](https://github.com/tesseract-ocr/tesseract/wiki)
1. [Meraki](https://meraki.cisco.com) administrator dashboard access and accompanying X-Cisco-Meraki-API-Key
1. [WebEx Teams](https://developer.webex.com) account with bot integration created

## Installation and run

```
$ python3 -m venv meraki_proVision_bot
$ pip install -r requirements.txt
$ python meraki_proVision_bot.py -u <url of webserver>
```

## Usage

In WebEx teams, find the bot you've created and direct Message it "Hi" or "Help".  Messaging prompts should allow follow on activities. 

## TODO
1. Improved error handling
1. Implement creating SSID when MR device is shown
1. Implement "Add" device
1. Implement "Remove" device
1. Implement "Delete" network

