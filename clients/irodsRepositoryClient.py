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

class irodsRepositoryClient():

    def __init__(self, envFile, apiToken, apiUrl):
        self.session = iRODSSession(irods_env_file=envFile)
        self.apiToken = apiToken
        self.apiUrl = apiUrl

    def collSize(self, collPath):
        coll = self.session.collections.get(collPath)
        size = sum([obj.size for obj in coll.data_objects])
        return size

    def collValidation(self, collPath):
        '''
        Checks whether collection is not empty and is not a nested collection.
        Returns list of error messages.
        '''
        coll = self.session.collections.get(collPath)
        errorMsg = []
        if coll.subcollections != []:
            errorMsg.append('PUBLISH ERROR: Collection contains subcollections.')
        if coll.data_objects == []:
            errorMsg.append('PUBLISH ERROR: Collection does not contain data.')
        return errorMsg

    def localCopyData(self, collPath, filepath = '/tmp'):
        '''
        Makes a local copy of the data files in the iRODS collection.
        '''
        coll = self.session.collections.get(collPath)
        filepath = filepath + "/" + coll.name
        try:
            print "Remove old data: ", filepath
            shutil.rmtree('filepath')
        except OSError:
            print filepath, "does not exist." 
        os.makedirs(filepath)
        
        for obj in coll.data_objects:
            buff = session.data_objects.open(obj.path, 'r').read()
            with open(filepath+'/'+obj.name, 'wb') as f:
                f.write(buff)

        return filepath

    def closeCollection(self, collPath):
        '''
        Set permission to read only for group 'public'.
        Get list of users who created the data. The original creator of the data can be retrieved with obj.owner_name.
        Script should be executed by a service account for data publishing (role data steward).
        '''
        coll = self.session.collections.get(collPath)
        acl = iRODSAccess('read', coll.path, 'public', self.session.zone)
        owners = ()
        self.session.permissions.set(acl)
        for obj in coll.data_objects:
            acl = iRODSAccess('read', obj.path, 'public', self.session.zone)
            self.session.permissions.set(acl)
            owners.add(obj.owner_name)

        return owners
            

        return False

    def openCollection(self, collPath, owners):
        '''
        Open collection for writing to certain iRODS users.
        '''
        coll = self.session.collections.get(collPath)
        for owner in owners:
            acl = iRODSAccess('write', coll.path, owner, self.session.zone)
            self.session.permissions.set(acl)
            for obj in coll.data_objects:
                acl = iRODSAccess('write', obj.path, owner, self.session.zone)
                self.session.permissions.set(acl)

        return 
            
    def b2shareMetaValidation(self, collPath):
        '''
        Checks whether necessary keys for the B2SHARE general template are defined as iRODS metadata on collection level.
        Expected keys:  PID --> epic PID from B2SAFE
                        CREATOR --> Name of the author of the data
        Rejected when expected keys are not defined or have empty values and 
        when data has been published to B2SHARE, i.e. there is a non-empty entry for PID/B2SHARE.
        Returns a list of error messages
        '''
        coll = self.session.collections.get(collPath)
        errorMsg = []
        keys = [i.name for i in coll.metadata.items() if i.value != '']
        if 'PID' not in keys:
            errorMsg.append('B2SHARE PUBLISH ERROR: Missing Metadata PID.')
        if 'CREATOR' not in keys:
            errorMsg.append('B2SHARE PUBLISH ERROR: Missing Metadata CREATOR.')
        if 'PID/B2SHARE' in keys:
            errorMsg.append('B2SHARE PUBLISH ERROR: Data is already published.')
        return errorMsg

    def b2shareMetaMap(self, collPath):
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
        coll = self.session.collections.get(collPath)

        metaMap = {}
        metaMap['seriesinformation'] = 'iRODS collection'
        metaMap['pidtype'] = 'EPIC'
        metaMap['title'] = '' 
        metaMap['creator'] = ''
        metaMap['identifier'] = ''
        metaMap['description'] = ''

        for item in coll.metadata.items():
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
            metaMap['title'] = coll.name
    
        return metaMap

    def getMemberNames(self, collPath):
        '''
        Retrieves either the PIDs of the single files in a collection or their object names.
        '''
        coll = self.session.collections.get(collPath)
        names = [obj.name for obj in coll.data_objects]
        pids = [i.value for obj in coll.data_objects for i in obj.metadata.items() if i.name == 'PID']
        members = ["File: "+ n +"; PID: http://hdl.handle.net/"+p+"?noredirect" for (n, p) in zip (names, pid)]

        return members


 
