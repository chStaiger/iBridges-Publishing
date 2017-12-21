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
        self.mdUpdate('SERIESINFORMATION', 'iRODS Collection '+ self.coll.path)
        self.md     = self.mdGet()

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
            errorMsg.append('PUBLISH ERROR: Data is already published.')
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

        cmd = 'iticket create read ' + self.coll.path
        p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out == '':
            errorMsg.append('TICKET ERROR: No ticket created '+ err)
            return tickets, errorMsg

        msg = self.mdUpdate('TICKET', out.split(':')[1].strip())
        tickets[self.coll.path] = out.split(':')[1].strip()
        self.mdUpdate('TECHNICALINFO', '{"irods_host": "'+self.session.host \
            + '", "irods_port": 1247, "irods_user_name": "anonymous", "irods_zone_name": "' \
            + self.session.zone+ '"}; iget/ils -t <ticket> ' + self.coll.path )

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

    def assignPID(self, pidClient, all = True):
        '''
        Creates epic PIDs for the collection and all its members.
        Returns a dictionary mapping from iRODS paths to PIDs.
        pidCredentials - instance of B2Handle EUDATHandleClient.
        '''
        pids = {}
        #TODO: mint real PIDs
        pid = str(uuid.uuid1())
        self.mdUpdate("PID", pid)
        pids[self.coll.name] = pid

        if all:
            for obj in self.coll.data_objects:
                pid = str(uuid.uuid1())
                obj.metadata.add("PID", pid)
                pids[obj.name] = pid

        return pids

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

    def mdUpdate(self, key, value):
        '''
        Update metadata of collection.
        '''
        if key in self.coll.metadata.keys():
            print 'METADATA INFO: Collection has already metadata with key: ' + key
            print 'METADATA INFO: Update metadata entry.'
            for item in self.coll.metadata.items():
                if item.name == key:
                    self.coll.metadata.remove(item)
        self.coll.metadata.add(key, value)
        self.md = self.mdGet()

        return ['METADATA ADDED; '+key+' '+value]

    def mdGet(self):
        '''
        Reformatting od all metadata of the collection into a python dictionary.
        '''
        metadata = {}
        for item in self.coll.metadata.items():
            metadata[item.name] = item.value

        return metadata
    
    def getMDall(self, key):
        '''
        Fetches all metadata with with a certain key from all members in a collection.
        It assumes that the key is only present once.
        Returns a dictionary iRODS path --> value
        '''
        metadata = {}
        if key in self.coll.metadata.keys():
            metadata[self.coll.path] = self.coll.metadata.get_one(key).value
        for obj in self.coll.data_objects:
            if key in obj.metadata.keys():
                metadata[obj.path] = obj.metadata.get_one(key).value

        return metadata
