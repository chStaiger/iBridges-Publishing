"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""

# Integrating B2SHARE and B2SAFE as a user
# 

import json
import requests
import os
import subprocess

API_TOKEN="XXXXXXXXXXXXXXXXXXXXX"
API_URL = "https://trng-b2share.eudat.eu/api/"
COMMUNITY_ID = "0c97d6d2-88da-473a-8d30-2f4e730ed4a2" #EPOS
COMMUNITY_ID = "e9b9792e-79fb-4b07-b6b4-b9c2bd06d095" #B2SHARE

# Download all data in a record from B2SHARE
#######################################################################
#NOTE: The B2SHARE API deals with lower case ids, but "home"/records/id
#lists id with capital letters.
r = requests.get('https://trng-b2share.eudat.eu/api/records/755f9026f1c241c9b3cb3e1abb322bce')

result = r.json()
title = result['metadata']['titles'][0]['title']

#download directory
folder = "B2SHARE_files"
os.mkdir(folder)

pid_dict = dict()
for entry in result['files']:
    pid_dict[entry['key'].replace(' ', '-')] = entry['ePIC_PID']

#download by PID NOTE: Does not work in test instance since no actionable PIDs
for entry in result['files']:
    content = requests.get(entry['ePIC_PID'])
    if content.status_code in range(200, 300):
        #save content as file
        with open(folder+"/"+entry['key'].replace(' ', '-'), 'wb') as out:
            out.write(content.content)

#download by B2SHARE path
resultfiles = requests.get(result['links']['files']).json()
for entry in resultfiles['contents']:
    content = requests.get(entry['links']['self'])
    if content.status_code in range(200, 300):
        with open(folder+"/"+entry['key'].replace(' ', '-'), 'wb') as out:
            out.write(content.content)
    
# Upload to iRODS/B2SAFE
#Connect to iRODS
#Create iRODS collection with "Title"

import getpass
pw = getpass.getpass().encode('base64')
from irods.session import iRODSSession
# If .irods is present
sess = iRODSSession(irods_env_file=os.environ['HOME']+'/.irods/irods_environment.json')
# else
sess = iRODSSession(host='alice-centos', port=1247, user='irods-user1', password=pw.decode('base64'), zone='aliceZone')

#iput -K 
import irods.keywords as kw
options = {kw.REG_CHKSUM_KW: ''}
iPath = '/'+sess.zone+'/home/'+sess.username+'/publish'
newColl = sess.collections.create(iPath)
print "Upload data from ", folder, "to iROD collection", iPath

for fname in os.listdir(folder):
    obj = sess.data_objects.create(iPath+'/'+fname)
    with open(folder+'/'+fname, 'r') as f:
        content = f.read()
    with obj.open('w', options) as obj_desc:
        obj_desc.write(content)
    #add metadata to files
    obj.metadata.add('EUDAT/ROR', pid_dict[fname][22:])

#check metadata
for fname in os.listdir(folder):
    obj = sess.data_objects.get(iPath+'/'+fname)
    print obj.name
    print obj.checksum
    print obj.metadata.items()
    print

# Upload a collection from B2SAFE to B2SHARE
###############################################################################
#Replication creates metadata in iCAT
#Transfer fields: PID, EUDAT/ROR and EUDAT/REPLICA to B2SHARE

#Data will stay in B2SAFE
#   -link via PID
#   -copy some B2SAFE metadata to B2SHARE metadata: EUDAT/ROR (mandatory), EUDAT/REPLICA
#       EUDAT/REPLICA: might change over time when more replicas are created --> update if mentioned in B2SHARE

create_draft_url = API_URL + "records/?access_token=" + API_TOKEN
#data = '{"titles":[{"title":"Collection from B2SAFE"}], "community":"' + COMMUNITY_ID + '", "open_access":true, "community_specific": {}}'
data = '{"titles":[{"title":"Single files from B2SAFE - linked by PID"}], "community":"' + COMMUNITY_ID + '", "open_access":true, "community_specific": {}}'
headers = {"Content-Type":"application/json"}

draft = requests.post(url = create_draft_url,
                headers=headers,
                data = data )

assert draft.status_code in range(200, 300)

record_id = draft.json()['id']
print("Record created with id: " + record_id)

#2a. Get PIDs for files from iRODS - https://trng-b2share.eudat.eu/records/7e956cd598c448dc8384954994a8a922
#These PIDs should be listed instead of creating new PIDs
#NOTE: The python client does not seem to be working for remote data objects
#https://github.com/irods/python-irodsclient/issues/98
#remotePath = "/bobZone/home/"+sess.username+"#"+sess.zone+'/b2replication'
iPath = '/'+sess.zone+'/home/'+sess.username+'/publish'
iColl = sess.collections.get(iPath)

# Get all PIDs for root collection, subcollections and data objects
objPIDs = {}
objRORs = {}
collPIDs = {}
collRORs = {} 
for srcColl, subColls, objs in iColl.walk():
    print objs
    for obj in objs:
        for item in obj.metadata.items():
            if item.name == "PID":
                print obj.path, ':', item.value
                objPIDs[obj.path] = item.value
            elif item.name == "EUDAT/ROR":
                print obj.path, ':', item.value
                objRORs[obj.path] = item.value
            else:
                continue
        assert obj.path in objPIDs
    for item in srcColl.metadata.items():
        if item.name == "PID":
            print srcColl.path, ':', item.value
            collPIDs[srcColl.path] = item.value
        elif item.name == "EUDAT/ROR":
            print srcColl.path, ':', item.value
            collRORs[srcColl.path] = item.value
        else:
            continue
    assert srcColl.path in collPIDs

PIDs = dict()
RORs = dict()
PIDs.update(objPIDs)
PIDs.update(collPIDs)
RORs.update(objRORs)
RORs.update(collRORs)

assert PIDs != {}

# Add PIDs as metadata
# Collection PID as description; single PIDs as TableOfContents
patch_url = API_URL + "records/" + record_id + "/draft?access_token=" + API_TOKEN
patch = '[{"op":"add","path":"/descriptions","value":[{"description":"B2SAFE collection: '+str('PID: '+PIDs[iPath])+'", "description_type":"SeriesInformation"},{"description":"B2SAFE coll/DO PIDs: '+str(PIDs)+'", "description_type":"TableOfContents"}]}]'
headers = {"Content-Type":"application/json-patch+json"}
response = requests.patch(url=patch_url, headers=headers, data=patch)

assert response in range(200, 300)

# Finalise and publish
patch = '[{"op":"add", "path":"/publication_state", "value":"submitted"}]'
response = requests.patch(url=patch_url, headers=headers, data=patch)

# Notes
# Data object copies in iRODS:
# sess.data_objects.copy('/aliceZone/home/irods-user1/publish/b2safe.png', '/aliceZone/home/irods-user1/b2safe-copy.png')
