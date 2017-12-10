#!/usr/bin/env python 

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""
from irods.session import iRODSSession
from irods.access import iRODSAccess
import os
import shutil
import requests
import getpass
import uuid

class irodsRepositoryClient():

    def __init__(self, envFile, apiToken, apiUrl, communityId, collection = 'public'):
        if envFile == '':
            #workaround for testing and when icommands not available
            pw = getpass.getpass().encode('base64')
            self.session = iRODSSession(host='alice-centos', port=1247, user='b2share', 
                password=pw.decode('base64'), zone='aliceZone')
        else:
            self.session = iRODSSession(irods_env_file=envFile)
        self.apiToken = apiToken
        self.apiUrl = apiUrl
        self.draftId = ''
        self.community = communityId
        collPath = '/' + self.session.zone + '/home/' + collection
        self.coll = self.session.collections.get(collPath)
        print "Publish collection: ", self.coll.path
        print "Draft ID: ", self.draftId

    def collectionSize(self):
        size = sum([obj.size for obj in self.coll.data_objects])
        return size

    def collectionValidation(self):
        '''
        Checks whether self.coll.ction is not empty and is not a nested self.coll.ction.
        Returns list of error messages.
        '''
        errorMsg = []
        if self.coll.subcollections != []:
            errorMsg.append('PUBLISH ERROR: Collection contains subcollections.')
        if self.coll.data_objects == []:
            errorMsg.append('PUBLISH ERROR: Collection does not contain data.')
        return errorMsg

    def localCopyData(self, path = '/tmp'):
        '''
        Makes a local copy of the data files in the iRODS self.coll.ction.
        '''
        
        path = path + "/" + self.coll.name
        try:
            print "Remove old data: ", path
            shutil.rmtree(path)
        except OSError:
            print path, "does not exist." 
        os.makedirs(path)
        
        for obj in self.coll.data_objects:
            buff = self.session.data_objects.open(obj.path, 'r').read()
            with open(path+'/'+obj.name, 'wb') as f:
                f.write(buff)

        return path

    def assignTicket(self, all = True):
        '''
        Creates irods tickets in read-mode  fro the self.coll.ction and all its members. 
        Ticket can be used in metalnx or wth the icommands to download data.
        Note: Not yet available in python client, hence icommands wrapper!
        Returns a dictionary mapping from iRODS paths to tickets
        '''
        tickets = {}

        return tickets

    def assignPID(self, pidCredentials, all = True):
        '''
        Creates epic PIDs for the collection and all its members.
        Returns a dictionary mapping from iRODS paths to PIDs.
        pidCredentials - instance of B2Handle EUDATHandleClient.
        '''
        pids = {}
        #TODO: mint real PIDs
        pid = str(uuid.uuid1())
        self.coll.metadata.add("PID", pid)
        pids[self.coll.name] = pid

        if all:
            for obj in self.coll.data_objects:
                pid = str(uuid.uuid1())
                obj.metadata.add("PID", pid)
                pids[obj.name] = pid

        return pids

    def closeCollection(self):
        '''
        Set permission to read only for group 'public'.
        Get list of users who created the data. The original creator of the data can be retrieved with obj.owner_name.
        Script should be executed by a service account for data publishing (role data steward).
        '''
        
        acl = iRODSAccess('read', self.coll.path, 'public', self.session.zone)
        owners = set()
        self.session.permissions.set(acl)
        for obj in self.coll.data_objects:
            acl = iRODSAccess('read', obj.path, 'public', self.session.zone)
            self.session.permissions.set(acl)
            acl = iRODSAccess('null', obj.path, obj.owner_name, self.session.zone)
            self.session.permissions.set(acl)
            acl = iRODSAccess('read', obj.path, obj.owner_name, self.session.zone)
            self.session.permissions.set(acl)
            owners.add(obj.owner_name)

        return owners
            
    def openCollection(self, owners):
        '''
        Open self.coll.ction for writing to certain iRODS users.
        '''
        
        for owner in owners:
            acl = iRODSAccess('write', self.coll.path, owner, self.session.zone)
            self.session.permissions.set(acl)
            for obj in self.coll.data_objects:
                acl = iRODSAccess('write', obj.path, owner, self.session.zone)
                self.session.permissions.set(acl)

        return 
            
    def b2shareMetaValidation(self):
        '''
        Checks whether necessary keys for the B2SHARE general template are defined as iRODS metadata on self.coll.ction level.
        Expected keys:  PID --> epic PID from B2SAFE
                        CREATOR --> Name of the author of the data
        Rejected when expected keys are not defined or have empty values and 
        when data has been published to B2SHARE, i.e. there is a non-empty entry for PID/B2SHARE.
        Returns a list of error messages
        '''
        
        errorMsg = []
        keys = [i.name for i in self.coll.metadata.items() if i.value != '']
        if 'PID' not in keys:
            errorMsg.append('B2SHARE PUBLISH ERROR: Missing Metadata PID.')
        if 'CREATOR' not in keys:
            errorMsg.append('B2SHARE PUBLISH ERROR: Missing Metadata CREATOR.')
        if 'B2SHARE/DOI' in keys:
            errorMsg.append('B2SHARE PUBLISH ERROR: Data is already published.')
        return errorMsg

    def b2shareMetaMap(self):
        '''
        Example metadata mapping from iRODS metadata to B2SHARE.
        Extracts values from iRODS metadata and maps it to B2SHARE keywords from the "B2SHARE generic" community.
        Accepted keys:
        TITLE --> titles:title
        CREATOR --> contributors:creator_name
        PID --> alternate_identifiers:alternate_identifier; alternate_identifier_type = EPIC
        DESCRIPTION --> descriptions:description; description_type=Abstract
        PIDs of data objects or namesof data objects are stored in Keywords --> keywords:[items]
        '''

        metaMap = {}
        metaMap['seriesinformation'] = 'iRODS collection'
        metaMap['pidtype'] = 'EPIC'
        metaMap['title'] = '' 
        metaMap['creator'] = ''
        metaMap['identifier'] = ''
        metaMap['description'] = ''

        for item in self.coll.metadata.items():
            if item.name == 'TITLE':
                metaMap['title'] = metaMap['title'] + item.value
            elif item.name == 'CREATOR':
                metaMap['creator'] = metaMap['creator'] + item.value
            elif item.name == 'PID':
                metaMap['identifier'] = metaMap['identifier'] + item.value
            elif item.name == 'DESCRIPTION':
                metaMap['description'] = metaMap['description'] + item.value
            else:
                print "Metadata not captured: ", item.name

        if metaMap['title'] == '':
            metaMap['title'] = self.coll.name
    
        return metaMap

    def addPublishID(self, repoName, id=''):
        '''
        Adds a PID from the repository to a collection in iRODS.
        key:    repoName/DOI: doi
                repoName/ID: id
        '''
        
        self.coll.metadata.add(repoName+'/DOI', self.doi)
        if id != '':
            self.coll.metadata.add(repoName+'/ID', id)
        
        return

    def createB2shareDraft(self, metaMap):
        '''
        Create a draft in B2SHARE
        '''
        errorMsg = []
        draftUrl = self.apiUrl + "records/?access_token=" + self.apiToken

        #create draft
        data = '{"titles":[{"title":"'+metaMap['title']+'"}], "community":"' + self.community + \
            '", "open_access":true, "community_specific": {}}'
        headers = {"Content-Type":"application/json"}
        request = requests.post(url = draftUrl, headers=headers, data = data )

        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not created: ' + request.status_code)
            return (errorMsg)
        self.draftId = request.json()['id']

        return (errorMsg)

    def getDraftUrl(self):
        return self.apiUrl + "records/" + self.draftId + "/draft?access_token=" + self.apiToken

    def patchB2shareDraft(self, metaMap, members = [], pids = {}, tickets = {}):
        '''
        Patching a draft and adding all metadata.
        '''
        errorMsg = []
        headers = {"Content-Type":"application/json-patch+json"}        

        #description
        patch = '[{"op":"add","path":"/descriptions","value":[{"description":"'+ metaMap['seriesinformation'] + \
            '", "description_type":"SeriesInformation"},{"description":"'+metaMap['description'] + \
            '", "description_type":"Abstract"}]}]'
        request = requests.patch(url=self.getDraftUrl(), headers=headers, data=patch)
        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with description. ' + str(request.status_code))
        print "added description"
        
        #creators
        patch = '[{"op":"add","path":"/creators","value":[{"creator_name":"' + metaMap['creator'] + '"}]}]'
        response = requests.patch(url=self.getDraftUrl(), headers=headers, data=patch)
        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with creators. ' + str(request.status_code))
        print "added creator"

        if pids != {}:
            print "adding pids"
            tmp = []
            for pid in pids:
                tmp.append('{"alternate_identifier": "'+pids[pid]+\
                    '", "alternate_identifier_type": "EPIC;'+\
                    self.coll.path+'/'+pid+'"}')
            patch = '[{"op":"add","path":"/alternate_identifiers","value":[' + ','.join(tmp)+']}]'
            request = requests.patch(url=self.getDraftUrl(), headers=headers, data=patch)
            if request.status_code not in range(200, 300):
                errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with pids. ' + str(request.status_code))
        else:
            print "adding coll pid"
            #collection identifier
            patch = '[{"op":"add","path":"/alternate_identifiers",' + \
                    '"value":[{"alternate_identifier":"'+ metaMap['identifier'] + '",' + \
                    '"alternate_identifier_type":"' + metaMap['pidtype'] +'; '+ \
                    self.coll.path +'"}]}]'
            request = requests.patch(url=self.getDraftUrl(), headers=headers, data=patch)
            if request.status_code not in range(200, 300):
                errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with iRODS identifier. ' + str(request.status_code))

        if tickets != {}:
            #patch     
            print "todo"

        return errorMsg

    def addDataB2shareDraft(self, localPath):
        '''
        Uploads local files to created draft.
        '''
        errorMsg = []
        r = json.loads(requests.get(self.getDraftUrl()).text)

        for f in os.listdir(localPath):
            upload_files_url = r['links']['files'] + "/" + f + "?access_token=" + self.apiToken
            files = {'file' : open(localPath+"/"+f, 'rb')}
            headers = {'Accept':'application/json','Content-Type':'application/octet-stream'}

            response = requests.put(url=upload_files_url,
                headers = headers, files = files )
            if response.status_code not in range(200, 300):
                errorMsg.append('B2SHARE PUBLISH ERROR: File not uploaded '+ \ 
                    localPath+"/"+f +', ' + str(request.status_code))
 
        return errorMsg

    def publishB2share(self):
        '''
        Publishes a B2SHARE draft
        '''
        b2shareId = ''
        patch = '[{"op":"add", "path":"/publication_state", "value":"submitted"}]'
        response = requests.patch(url=self.getDraftUrl(), headers=headers, data=patch)
        r = json.loads(requests.get(self.getDraftUrl()).text)    
        doi = r['metadata']['DOI']        

        return b2shareId


