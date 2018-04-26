#!/usr/bin/env python 

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""

from irodsPublishCollection import irodsPublishCollection
from b2shareDraft import b2shareDraft
from dataverseDraft import dataverseDraft
from irodsRepositoryClient import irodsRepositoryClient

import datetime

RED     = "\033[31m"
GREEN   = "\033[92m"
BLUE    = "\033[34m"
DEFAULT = "\033[0m"


#iRODS credentials and parameters
irodsEnvFile    = '' # .irods/irodsenviroment.json; if empty user password will be asked
collection	= '/aliceZone/home/public/b2share/myDeposit'

#B2SHARE credentials and parameters
apiToken        = '******************************************' 
apiUrl          = 'https://trng-b2share.eudat.eu/api/'
community       = 'e9b9792e-79fb-4b07-b6b4-b9c2bd06d095'

#Dataverse credentials and parameters
apiToken        = '******************************************'
apiUrl 	        = 'http://demo.dataverse.nl/'
alias           = 'a64b880c-408b-11e8-a58f-040091643b8b'

#Other parameters for publication
maxDataSize     = 2000 # in MB

# Instantiate iRODS

ipc = irodsPublishCollection(irodsEnvFile, collection, host = 'ibridges', 
                             user = 'ibridges', zone = 'ibridgesZone')

# Instantiate draft
draft = b2shareDraft(apiToken, apiUrl, community)
draft = dataverseDraft(apiToken, apiUrl, alias)

# Instantiate client
publishclient = irodsRepositoryClient(ipc, draft)
message = ['Upload to' + draft.repoName, str(datetime.datetime.now()), collection, '']

# Change ACLs for users to read only
owners = ipc.close()
message.append('OWNERS :' + str(owners))

# Validate whether to publish collection
print GREEN + 'Validate collection, create PIDs and Tickets.'
message.extend(publishclient.checkCollection())

if any(item.startswith(publishclient.draft.repoName + ' PUBLISH ERROR') for item in message) or \
    any(item.startswith('PUBLISH ERROR') for item in message):

    print RED + 'VALIDTION ERROR' + DEFAULT
    message.extend(publishclient.ipc.open(owners))
    print 'Create report: ' + publishclient.createReport(message, owners)    
    assert False

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
    assert False

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

