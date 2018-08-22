#!/usr/bin/env python

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""
import os
import logging
import subprocess

# iRODS imports
from irods.access import iRODSAccess

# PID imports
import uuid

from tempdir import Tempdir
from tempdir import buffered_read


class iRodsPublishCollection():
    argument_prefix = "irods"

    @staticmethod
    def add_arguments(parser):
        args = [('collection_prefix',
                 'prefix of the collection to be bridged'),
                ('env_file',
                 'path to irods env. file'),
                ('host',
                 'irods host'),
                ('http_endpoint',
                 'http or davrods endpoint'),
                ('user',
                 'irods user'),
                ('zone',
                 'irods zone')]
        for arg, h in args:
            parser.add_argument('--%s_%s' %
                                (iRodsPublishCollection.argument_prefix, arg),
                                type=str,
                                help=h)

    def __init__(self, collection, session, http_endpoint='', logger=None):
        self.session = session
        if logger is None:
            self.logger = logging.getLogger('ipublish')
        else:
            self.logger = logger
        self.collection_path = collection
        self.coll = self.session.collections.get(collection)
        self.md = self.mdGet()
        self.http = http_endpoint  # http or davrods endpoint

    @property
    def uri(self):
        return "irods://%s/%s" % (self.session.host, self.collection_path)

    @property
    def title(self):
        return self.md['TITLE']

    def size(self):
        size = sum([obj.size for obj in self.coll.data_objects])
        return size

    def isPublished(self, repoKeys):
        return len(set(self.coll.metadata.keys()).intersection(repoKeys)) > 0

    def validate(self, repoKeys=[]):
        '''
        Checks whether collection is not empty and is not a nested collection.
        repoKeys is a set of keys in te iRODS metadata that indicate,
        when present, that the data have already been published.
        '''
        ret = True
        if self.coll.subcollections != []:
            self.logger.error('PUBLISH: Collection contains subcollections.')
            ret = False
        if self.coll.data_objects == []:
            self.logger.error('PUBLISH: Collection does not contain data.')
            ret = False
        if self.isPublished(repoKeys):
            self.logger.error('PUBLISH: Data is already published:')
            for item in self.coll.metadata.items():
                self.logger.error(' metadata: %s:%s', item.name, item.value)
            ret = False
        return ret

    def assignSeriesInformation(self):
        self.mdUpdate('SERIESINFORMATION',
                      'iRODS Collection ' + self.coll.path)

    def assignTicket(self, all=True):
        '''
        Creates irods tickets for anonymous read access for the collection.
        Ticket can be used in metalnx or wth the icommands to download data.
        It also creates a metadata entry for the ticket in the metadata of
        the respective data object or collection to avoid long searches through
        the iCAT.
        Note: Not yet available in python client (v0.8),
        hence icommands wrapper!
        Returns a dictionary mapping from iRODS paths to tickets.
        Requires icommands!
        '''
        tickets = {}
        # iticket create read <obj path>
        # imeta add <obj path> TICKET <ticket>

        cmd = 'iticket create read ' + self.coll.path
        p = subprocess.Popen([cmd],
                             shell=True,  # @todo fix this: don't use shell
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out == '':
            self.logger.error('TICKET ERROR: No ticket created: %s ', err)
            return tickets, False

        self.mdUpdate('TICKET', out.split(':')[1].strip())
        tickets[self.coll.path] = out.split(':')[1].strip()
        self.mdUpdate('TECHNICALINFO',
                      '{"irods_host": "%s", "irods_port": %d, ' +
                      '"irods_user_name": "%s", "irods_zone_name": "%s"}; ' +
                      'iget/ils -t <ticket> %s'
                      % (self.session.host,
                         1247,
                         "anonymous",
                         self.session.zone,
                         self.coll.path))
        if not all:
            return tickets, True

        for obj in self.coll.data_objects:
            cmd = 'iticket create read ' + obj.path
            p = subprocess.Popen([cmd],
                                 shell=True,  # @todo don't use shell
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out == '':
                self.logger.error('TICKET ERROR: No ticket created %s', err)
                return tickets, False
            obj.metadata.add('TICKET', out.split(':')[1].strip())
            tickets[obj.path] = out.split(':')[1].strip()

        return tickets, True

    def assignPID(self, pidClient, all=True):
        '''
        Creates epic PIDs for the collection and all its members.
        Returns a dictionary mapping from iRODS paths to PIDs.
        pidCredentials - instance of B2Handle EUDATHandleClient.
        '''
        pids = {}
        # TODO: mint real PIDs
        # @todo: check if assignPID is required
        pid = str(uuid.uuid1())
        self.mdUpdate("PID", pid)
        pids[self.coll.name] = pid

        if all:
            for obj in self.coll.data_objects:
                pid = str(uuid.uuid1())
                obj.metadata.add("PID", pid)
                pids[obj.name] = pid

        return pids

    def close(self, owners=set()):
        '''
        Set permission to read only for group 'public'.
        Get list of users who created the data.
        The original creator of the data can be retrieved with obj.owner_name.
        Script should be executed by a service account for data publishing
        (role data steward).
        owners - set of all additinatiol users who have write access
        to the collection and data objects.
        '''

        # close each data object
        for obj in self.coll.data_objects:
            acl = iRODSAccess('read', obj.path, 'public', self.session.zone)
            self.session.permissions.set(acl)
            acl = iRODSAccess('read',
                              obj.path,
                              obj.owner_name,
                              self.session.zone)
            self.session.permissions.set(acl)
            for owner in owners:
                acl = iRODSAccess('read', obj.path, owner, self.session.zone)
                self.session.permissions.set(acl)
            owners.add(obj.owner_name)

        # close collection
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
            acl = iRODSAccess('write',
                              self.coll.path,
                              owner,
                              self.session.zone)
            self.session.permissions.set(acl)
            for obj in self.coll.data_objects:
                acl = iRODSAccess('write',
                                  obj.path,
                                  owner,
                                  self.session.zone)
                self.session.permissions.set(acl)

        return ['COLLECTION WRITE ACCESS: ' + str(owners)]

    def mdUpdate(self, key, value):
        '''
        Update metadata of collection.
        '''
        self.logger.debug('mdUpdate: {%s=%s}', key, value)
        if key in self.coll.metadata.keys():
            self.logger.warning('METADATA: ' +
                                'Collection has already metadata with key: %s'
                                % key)
            self.logger.warning('METADATA: Update metadata entry.')
            for item in self.coll.metadata.items():
                if item.name == key:
                    self.coll.metadata.remove(item)
        self.coll.metadata.add(key, value)
        self.md = self.mdGet()
        self.logger.info('METADATA ADDED {%s=%s}', key, value)
        # todo check if return value is needed
        # return ['METADATA ADDED; '+key+' '+value]

    def mdGet(self):
        '''
        Reformatting od all metadata of the collection
        into a python dictionary.
        '''
        metadata = {}
        for item in self.coll.metadata.items():
            metadata[item.name] = item.value

        return metadata

    def getMDall(self, key):
        '''
        Fetches all metadata with with a certain key
        from all members in a collection.
        It assumes that the key is only present once.
        Returns a dictionary iRODS path --> value
        '''
        metadata = {}
        if key in self.coll.metadata.keys():
            metadata[self.coll.path] = self.coll.metadata.get_all(key)[0].value
        for obj in self.coll.data_objects:
            if key in obj.metadata.keys():
                metadata[obj.path] = obj.metadata.get_all(key)[0].value

        return metadata

    def downloadCollection(self, remove=True):
        with Tempdir(prefix="ipublish_", remove=remove) as td:
            for obj in self.coll.data_objects:
                target = os.path.join(td, obj.name)
                self.downloadObject(obj.path, target)
                yield target

    def downloadObject(self, path, target):
        self.logger.debug('download object %s -> %s', path, target)
        with open(target, 'wb') as outfile:
            with self.session.data_objects.open(path, 'r') as infile:
                for buff in buffered_read(infile):
                    outfile.write(buff)
