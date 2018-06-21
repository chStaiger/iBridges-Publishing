#!/usr/bin/env python 

"""
@licence: Apache 2.0
@Copyright (c) 2018, Christine Staiger (SURFsara)
@author: Christine Staiger
"""

from irodsPublishCollection import irodsPublishCollection
from b2shareDraft import b2shareDraft
from dataverseDraft import dataverseDraft
from irodsRepositoryClient import irodsRepositoryClient

import datetime
import json
import pprint
import sys

RED     = "\033[31m"
GREEN   = "\033[92m"
BLUE    = "\033[34m"
DEFAULT = "\033[0m"

# Load credentials and parameters for iRODS and the repository
choice = input("Parameters file:")
parameters =  json.load(open(choice))
print BLUE, "Parameters: "
pprint.pprint(parameters)
print DEFAULT

print "Current collection:", parameters['collection'] 
choice = input("Change collection?(\"\"/\"path\")\n")

if choice != "":
    parameters['collection'] = choice

#Other parameters for publication
maxDataSize     = 2000 # in MB

# Instantiate iRODS

ipc = irodsPublishCollection(parameters['irodsEnvFile'], 
			     parameters['collection'], 
			     parameters['host'], 
			     parameters['user'], 
   			     parameters['zone'])

# Instantiate draft
choice = input("[1]: B2SHARE \n[2]: Dataverse\n")
if choice == 1:
    draft = b2shareDraft(parameters['apiToken'], parameters['apiUrl'], parameters['community'])
elif choice == 2:
    draft = dataverseDraft(parameters['apiToken'], parameters['apiUrl'], parameters['community'])
else:
    print RED, "Invalid input", DEFAULT
    sys.exit("Input error")

print draft.repoName

# Instantiate client
publishclient = irodsRepositoryClient(ipc, draft)
message = ['Upload to' + draft.repoName, str(datetime.datetime.now()), parameters['collection'], '']

# Change ACLs for users to read only
owners = ipc.close()
message.append('OWNERS :' + str(owners))

# Validate whether to publish collection
print GREEN + 'Validate collection, create PIDs and Tickets.'
message.extend(publishclient.checkCollection())

if 'PUBLISH ERROR: Data is already published.' in message:
    print RED + "Data already published " + DEFAULT + publishclient.ipc.md[draft.repoName+"/URL"] 
    print 'Create report: ' + publishclient.createReport(message, owners)
    sys.exit("Publication error")

if any(item.startswith(publishclient.draft.repoName + ' PUBLISH ERROR') for item in message) or \
    any(item.startswith('PUBLISH ERROR') for item in message):

    print RED + 'VALIDTION ERROR' + DEFAULT
    message.extend(publishclient.ipc.open(owners))
    print 'Create report: ' + publishclient.createReport(message, owners)    
    sys.exit("Metadata validation error")

print GREEN + "PIDs created." + DEFAULT
print GREEN + "Tickets created." + DEFAULT

print "Check report: "
print '\n'.join([str(i) for i in message])
print

# Create draft
print GREEN + 'Create repository draft.'

out = publishclient.draft.create(publishclient.ipc.md['TITLE'])
if out != None:
    message.extend(out)
    print 'Create report: ' + publishclient.createReport(message, owners)
    print RED + "Publication failed." + DEFAULT + "Draft not created." 
    sys.exit("Data and metadata upload error")

print GREEN + 'Patch with metadata and data' + DEFAULT
message.extend(['Draft URL', publishclient.draft.draftUrl, ''])
message.extend(publishclient.uploadToRepo(data = publishclient.ipc.size()/1000. < maxDataSize))
if any(item.startswith(publishclient.draft.repoName + ' PUBLISH ERROR') for item in message):
    print 'Create report: ' + publishclient.createReport(message, owners)
    print RED + 'Metadata/data upload failed'
    raw_input("Press Enter to continue...")
    print DEFAULT

raw_input(GREEN + "Press Enter to publish..." + DEFAULT)
message.extend(publishclient.publishDraft())

# Create final report
print 'Create report: ' + publishclient.createReport(message, owners)

