#!/usr/bin/env python 

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""

from irodsRepositoryClient import irodsRepositoryClient
from b2handle.clientcredentials import PIDClientCredentials
from b2handle.handleclient import EUDATHandleClient

irodsEnvFile    = ''
apiToken        = '******************************************' 
apiUrl          = 'https://trng-b2share.eudat.eu/api/'
community       = '9b9792e-79fb-4b07-b6b4-b9c2bd06d095'
collection      = 'public/b2share/publish' # iRODS collection to publish
maxDataSize     = 2000 # in MB
repoName        = 'B2SHARE'

# Instantiate
irc = irodsRepositoryClient(irodsEnvFile, apiToken, apiUrl, community, collection)

# Change ACLs for users to read only
owners = irc.closeCollection()

# Validate whether to publish collection
message = irc.collectionValidation()
message.extend(irc.b2shareMetaValidation())

if len(error) > 0:
    irc.createReport(message, owners)
    print "Collection not published:"
    print collection
    print message

    #open collection again so that users can add metadata
    irc.openCollection(owners)

    assert False

# According to your publishing policy assign PIDs or tickets
pids = {}
ec = '' #TODO code here to create a EUDATHandleClient from b2handle
pids = irc.assignPID(ec)

#TODO: example to create tickets
tickets = {}

# Create the metadata mapping
metaMap = irc.b2shareMetaMap()
m       = ['Metadata mapping']
m.extend([ k +':'+ v for k, v in metaMap.items() ])
m.append('')
message.extend(message)

# Create B2SHARE draft
out = irc.createB2shareDraft(metaMap)
if len(out) > 0:
    error.extend(out)
    irc.createReport(message, owners)
    
    print "Draft not created:" 
    print collection
    print out
    
    assert False

message.extend(['Draft URL', irc.getDraftUrl(), ''])

# Patch draft with metadata
message.extend(irc.patchB2shareDraft(metaMap, pids, tickets))

# Upload data if data is small
if irc.collectionSize()/1000. < maxDataSize:
    #download data from iRODS to local folder
    files = irc.localCopyData()
    #upload to B2SHARE
    message.extend(irc.addDataB2shareDraft(files))

# Create report for draft and send to user
irc.createReport(message, owners)

# If user is OK publish
doi = extend(irc)
message.extend(['', 'Datapublished under DOI', doi])
irc.addPublishID(repoName, doi, id=irc.draftId)
