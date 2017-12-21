#!/usr/bin/env python 

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""
from irodsPublishCollection import irodsPublishCollection
from b2shareDraft import b2shareDraft

import datetime

RED     = "\033[31m"
GREEN   = "\033[92m"
BLUE    = "\033[34m"
DEFAULT = "\033[0m"


#iRODS credentials and parameters
irodsEnvFile    = '' # .irods/irodsenviroment.json; if empty user b2share, password will be asked
collection	= '/aliceZone/home/public/b2share/myDeposit'

#B2SHARE credentials and parameters
apiToken        = '******************************************' 
apiUrl          = 'https://trng-b2share.eudat.eu/api/'
community       = 'e9b9792e-79fb-4b07-b6b4-b9c2bd06d095'

#Other parameters for publication
maxDataSize     = 2000 # in MB

# Instantiate iRODS
ipc = irodsPublishCollection(irodsEnvFile, collection)

# Instantiate B2SHARE draft
draft = b2shareDraft(apiToken, apiUrl, community)

message = ['Upload to' + draft.repoName, str(datetime.datetime.now()), collection, '']

# Change ACLs for users to read only
owners = ipc.close()

# Validate whether to publish collection
m = len(message)
message.extend(ipc.validate(repoKeys=[draft.repoName + '/DOI']))
if len(message) > m:
    print RED + "Publication failed." + DEFAULT + " Data is already published."
    message.extend(ipc.open(owners))
    print '\n'.join([str(i) for i in message])
    assert False 

# Check if all metadata is there
expectedKeys = draft.metaKeys
if set(expectedKeys).issubset(ipc.md.keys()):
    message.append('PUBLISH NOTE: all metadata defined: ' + str(expectedKeys))
else:
    print RED + "Publication failed!" + DEFAULT + "Create report."
    message.append('PUBLISH ERROR: metadata not defined: ' + str(set(expectedKeys).difference(ipc.md.keys())))
    message.extend(ipc.open(owners))
    print '\n'.join([str(i) for i in message])
    assert False

# According to your publishing policy assign PIDs or tickets
pids = ipc.getMDall('PID')
if pids == {}:
    ec = '' #TODO code here to create a EUDATHandleClient from b2handle
    pids = ipc.assignPID(ec)
message.extend(['PIDs for collection: ', str(pids)])
print GREEN + "PIDs created." + DEFAULT

tickets = ipc.getMDall('TICKET)
if tickets == {}:
    tickets, error = ipc.assignTicket()
    if error:
        message.extend(error)
        print RED + 'Assigning tickets failed' + DEFAULT
        message.extend(['Tickets for collection', str(tickets)])
        print '\n'.join([str(i) for i in message])
        assert false
                       
print GREEN + "Tickets created." + DEFAULT

# Create B2SHARE draft
out = draft.create(ipc.md['TITLE'])
if out != '':
    message.extend(out)
    #create report
    #TODO 
    print RED + "Publication failed." + DEFAULT + "Draft not created." 
    print '\n'.join([str(i) for i in message])
    assert False

message.extend(['Draft URL', draft.draftUrl, ''])

# Patch draft with metadata
message.extend(draft.patchGeneral(ipc.md))
# Patch with pids
message.extend(draft.patchPIDs(pids))
# Patch with tickets
message.extend(draft.patchTickets(tickets))

# Upload data if data is small
if ipc.size()/1000. < maxDataSize:
    #download data from iRODS to local folder
    #TODO
    #folder = irc.localCopyData()
    #upload to B2SHARE
    #message.extend(draft.uploadData(folder))

# Create report for draft and send to user
#irc.createReport(message, owners)

# If user is OK publish
doi = draft.publish()
message.extend(['', 'Data published under DOI', doi])
message.append(ipc.mdUpdate(draft.repoName+"/DOI", doi))
message.append(ipc.mdUpdate(draft.repoName+"ID", draft.draftId))

# Create final report


