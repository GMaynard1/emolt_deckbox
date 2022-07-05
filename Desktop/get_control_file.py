## This script downloads the control file from the eMOLT development API

import requests

## Prompt the user for a vessel name
vesselname=input("Please enter vessel name: ")

## Standardize the vessel name
vesselname=vesselname.replace(" ","_")
vesselname=vesselname.replace("F/V","")

## Read in the API connection info
with open ("/home/pi/Documents/config.yml","r") as yamlfile:
  API_config=yaml.load(yamlfile, Loader=yaml.FullLoader)

address = API_config['default']['IP']

## Form the URL
url = 'http://'+address+'/getControl_File?vessel='+vesselname

## Request the control file
r = requests.get(url, allow_redirects=True)

## Save the control file to the appropriate location
open('/home/pi/Desktop/setup_rtd.py', 'wb').write(r.content)
