#!/usr/bin/env python 

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""
#iRODS imports
from irods.session import iRODSSession
from irods.access import iRODSAccess
import irods.keywords as kw

#iRODS tickets
import subprocess

#File and password handling
import os
import shutil
import getpass

#PID imports
import uuid
from b2handle.handleclient import EUDATHandleClient
from b2handle.clientcredentials import PIDClientCredentials

#B2SHARE imports
import requests
import json

class irodsPublishCollection():
    def __init__(self, envFile, collPath):
        if envFile == '':
            #workaround for testing and when icommands not available
            pw = getpass.getpass().encode('base64')
            self.session = iRODSSession(host='alice-centos', port=1247, user='b2share',
                password=pw.decode('base64'), zone='aliceZone')
        else:
            self.session = iRODSSession(irods_env_file=envFile)
        self.coll   = self.session.collections.get(collPath)
        self.objs   = self.coll.data_objects
        self.md     = self.coll.metadata.items() 

    def size(self):
        size = sum([obj.size for obj in self.coll.data_objects])
        return size

    def validate(self, repoKeys = []):
        '''
        Checks whether collection is not empty and is not a nested collection.
        repoKeys is a set of keys in te iRODS metadata that indicate, when present, 
        that the data have already been published.
        '''
        errorMsg = []
        if self.coll.subcollections != []:
            errorMsg.append('PUBLISH ERROR: Collection contains subcollections.')
        if self.coll.data_objects == []:
            errorMsg.append('PUBLISH ERROR: Collection does not contain data.')
        if len(set(self.coll.metadata.keys()).intersection(repoKeys)) > 0:
            errorMsg.append('REPOSITORY PUBLISH ERROR: Data is already published.')
            for item in self.coll.metadata.items():
                errorMsg.append(item.name+': '+item.value)

        return errorMsg

    def assignTicket(self, all = True):
        '''
        Creates irods tickets for anonymous read access for the collection.
        Ticket can be used in metalnx or wth the icommands to download data.
        It also creates a metadata entry for the ticket in the metadata of the respective 
        data object or collection to avoid long searches through the iCAT.
        Note: Not yet available in python client (v0.8), hence icommands wrapper!
        Returns a dictionary mapping from iRODS paths to tickets.
        Requires icommands!
        '''
        tickets = {}
        errorMsg = []        

        #iticket create read <obj path>
        #imeta add <obj path> TICKET <ticket>
        if 'TICKET' in self.coll.metadata.keys()
            errorMsg.append('TICKET ERROR: Ticket already exists.')
            return tickets, errorMsg 
        
        p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out == '':
            errorMsg.append('TICKET ERROR: No ticket created '+ err)
            return tickets, errorMsg
        
        msg = self.mdAdd('TICKET', out.split(':')[1].strip())
        tickets[self.coll.path] = out.split(':')[1].strip()       

        if not all:
            return tickets, errorMsg
        
        for obj in self.coll.data_objects:
            cmd = 'iticket create read ' + obj.path
            p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out == '':
                errorMsg.append('TICKET ERROR: No ticket created '+ err)
                return tickets, errorMsg 
            obj.metadata.add('TICKET', out.split(':')[1].strip())  
            tickets[obj.path] = out.split(':')[1].strip()     
    
        return tickets, errorMsg

    def close(self, owners = set()):
        '''
        Set permission to read only for group 'public'.
        Get list of users who created the data. The original creator of the data can be retrieved with obj.owner_name.
        Script should be executed by a service account for data publishing (role data steward).
        owners - set of all additinatiol users who have write access to the collection and data objects.        
        '''

        #close each data object
        for obj in self.coll.data_objects:
            acl = iRODSAccess('read', obj.path, 'public', self.session.zone)
            self.session.permissions.set(acl)
            acl = iRODSAccess('read', obj.path, obj.owner_name, self.session.zone)
            self.session.permissions.set(acl)
            for owner in owners:
                acl = iRODSAccess('read', obj.path, owner, self.session.zone)    
                self.session.permissions.set(acl)
            owners.add(obj.owner_name)

        #close collection
        acl = iRODSAccess('read', self.coll.path, 'public', self.session.zone)
        self.session.permissions.set(acl)
        for owner in owners:
            acl = iRODSAccess('read', self.coll.path, owner, self.session.zone)
            self.session.permissions.set(acl)

        return owners

    def open(self, owners):
        '''
        Open collection for writing to certain iRODS users (owners).
        '''
        for owner in owners:
            acl = iRODSAccess('write', self.coll.path, owner, self.session.zone)
            self.session.permissions.set(acl)
            for obj in self.coll.data_objects:
                acl = iRODSAccess('write', obj.path, owner, self.session.zone)
                self.session.permissions.set(acl)

        return ['COLLECTION WRITE ACCESS: ' + str(owners)]

    def mdAdd(self, key, value):
        '''
        Update metadata of collection.
        '''
        if key in self.coll.metadata.keys():
            return ['METADATA ERROR: Collection has already metadata with key: ' + key]
        self.coll.metadata.add(key, value)
        self.md = self.coll.metadata.items()
    
        return ['METADATA ADDED; '+key+' '+value]

class B2SHAREdraft():
 
    def __init__(self, apiToken, apiUrl, communityId, draftUrl = ''):
        self.apiToken   = apiToken
        self.apiUrl     = apiUrl
        self.community  = communityId
        self.draftUrl   = draftUrl

    def create(self, title):
        '''
        Create a draft in B2SHARE with some minimal metadata.
        '''
        if self.draftUrl != '':
            print "Draft already created: " + self.draftUrl
            return ['B2SHARE PUBLISH ERROR: Draft already exists: ' + self.draftUrl]

        errorMsg = []
        createUrl = self.apiUrl + "records/?access_token=" + self.apiToken

        #create draft
        data = '{"titles":[{"title":"'+title+'"}], "community":"' + self.community + \
            '", "open_access":true, "community_specific": {}}'
        headers = {"Content-Type":"application/json"}
        request = requests.post(url = createUrl, headers=headers, data = data )

        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not created: ' + str(request.status_code))
            return (errorMsg)
        self.draftUrl = self.apiUrl + "records/" + request.json()['id'] + \
            "/draft?access_token=" + self.apiToken
        self.draftId = request.json()['id']

        return (errorMsg)    

    def patch():
        return

    def uploadData(self, folder):
        '''
        Uploads local files from a folder to the draft.
        '''
        errorMsg = []
        r = json.loads(requests.get(self.draftUrl).text)

        for f in os.listdir(localPath):
            upload_files_url = r['links']['files'] + "/" + f + "?access_token=" + self.apiToken
            files = {'file' : open(folder+"/"+f, 'rb')}
            headers = {'Accept':'application/json',
                'Content-Type':'application/octet-stream --data-binary'}
            response = requests.put(url=upload_files_url,
                headers = headers, files = files )
            if response.status_code not in range(200, 300):
                errorMsg.append('B2SHARE PUBLISH ERROR: File not uploaded ' +
                    localPath+"/"+f +', ' + str(request.status_code))

        return errorMsg    

    def publish(self):
        '''
        Publishes a B2SHARE draft.
        '''
        headers = {"Content-Type":"application/json-patch+json"}
        patch = '[{"op":"add", "path":"/publication_state", "value":"submitted"}]'
        response = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        r = json.loads(requests.get(self.draftUrl).text)
        doi = r['metadata']['DOI']

        return doi     

class irodsRepositoryClient():

    def __init__(self, collection, draft):
        
        self.draft = draft
        self.ipc = collection
        print "Publish collection: ", self.coll.path
        print "Draft ID: ", self.draftId

    def localCopyData(self, path = '/tmp'):
        '''
        Makes a local copy of the data files in the iRODS self.coll.ction.
        '''
        
        path = path + "/" + self.ipc.coll.name
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

    def assignPID(self, pidClient, all = True):
        '''
        Creates epic PIDs for the collection and all its members.
        Returns a dictionary mapping from iRODS paths to PIDs.
        pidCredentials - instance of B2Handle EUDATHandleClient.
        '''
        pids = {}
        #TODO: mint real PIDs
        pid = str(uuid.uuid1())
        ipc.coll.mdUpdate("PID", pid)
        pids[self.coll.name] = pid

        if all:
            for obj in ipc.coll.data_objects:
                pid = str(uuid.uuid1())
                obj.metadata.add("PID", pid)
                pids[obj.name] = pid

        return pids

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

    def addPublishID(self, repoName, doi, id=''):
        '''
        Adds a PID from the repository to a collection in iRODS.
        key:    repoName/DOI: doi
                repoName/ID: id
        '''
        
        self.ipc.mdUpdate(repoName+'/DOI', doi)
        if id != '':
            self.ipc.mdUpdate(repoName+'/ID', self.draftId)
        
    def patchB2shareDraft(self, metaMap, pids = {}, tickets = {}):
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

    def createReport(self, content, owners=[]):
        '''
        Creates a report file for the users in /zone/home/public.
        Naming convention: user1-user2-..._collection.status
        content - list of strings
        owners - iterable 
        '''
        message = '\n'.join([str(i) for i in content])
        users   = '-'.join(owners)
        iPath   = '/'+ipc.session.zone+'/home/public/'+users+'_'+self.coll.name+'.status'
        
        try:
            obj = self.session.data_objects.create(iPath) 
        except Exception:
            obj = self.session.data_object.get(iPath)
        with obj.open('w') as obj_desc:
            obj_desc.write(message)

        for user in owners:
            acl = iRODSAccess('write', iPath, user, self.session.zone)
            self.session.permissions.set(acl) 
        
    
