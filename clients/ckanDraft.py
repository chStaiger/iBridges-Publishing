#!/usr/bin/env python

"""
@licence: Apache 2.0
@Copyright (c) 2018, Christine Staiger (SURFsara)
@author: Christine Staiger
"""
from urllib2 import quote
import urllib2
import simplejson as json
from urllib2 import urlopen, Request
import uuid
import os

class ckanDraft():

    def __init__(self, apiToken, apiUrl, ckanOrg, ckanID = '', ckanGroup = ''):
        self.apiToken   = apiToken
        self.apiUrl     = apiUrl #server, e.g. hostname:8080/api/3
        self.ckanOrg  	= ckanOrg
        self.ckanGroup   = ckanGroup
        self.ckanID	= ckanID # ckan name
        if self.ckanID == '':
            self.ckanID = str(uuid.uuid1())
        self.repoName   = 'CKAN'
        self.metaKeys   = ['TITLE', 'ABSTRACT', 'CREATOR']
        self.draftUrl   = 'http://{api}/dataset/{id}'.format(api=self.apiUrl.split('/api')[0], id=self.ckanID) 

    def create(self, title):
        '''
        Create a draft in CKAN with some minimal metadata.
        '''
        action = "package_list"
        action_url = 'http://{api}/action/{action}'.format(api=self.apiUrl, action=action)
        print "Listing packages: ", action_url
        response = urllib2.urlopen(action_url)
        response_dict = json.loads(response.read())
        
        if self.ckanID in response_dict['result']:
            print "Draft already created: " + self.ckanID
            return ['CKAN PUBLISH INFO: Draft already exists: ' + self.ckanID]
 
        #create draft
        action = 'package_create' # package_update
        action_url = 'http://{api}/action/{action}'.format(api=self.apiUrl, action=action)
        data = {'title': title, 'owner_org': self.ckanOrg, 'name': self.ckanID}
        if self.ckanGroup != '':
            data['group'] = self.ckanGroup
            data['groups'] = [{'name': self.ckanGroup}]
        data_string = quote(json.dumps(data))
        request = Request(action_url, data_string)
        request.add_header('Authorization', self.apiToken)

        try:
            response = urlopen(request) # if name already exists or is not given throws 409
            self.data = data
            self.draftUrl = 'http://{api}/dataset/{id}'.format(api=self.apiUrl.split('/api')[0], id=self.ckanID)
            return 
        except:
            return ["Draft not created."] 

    def patchGeneral(self, metadata, collPath = 'irods'):
        '''
        Adds and updates metadata to a CKAN draft.
        Mandatory metadata entries: CREATOR, TITLE, ABSTRACT, SUBJECT
        If data is not uploaded it is advised to provide pids pointing to the data in iRODS or
        to provide tickets for anonym ous data download.
        NOTE: If the draft already contains files, the update of metadata will fail.
        Parameters:
        metadata = ipc.mdGet()
        collPath = iRODS path or webdav access to collection or data object
        '''
        errorMsg = []
        curMeta = self.data
        print curMeta

        # CREATOR --> author
        curMeta['author'] = metadata['CREATOR'] 
    
        # ABSTRACT --> notes
        curMeta['notes'] = metadata['ABSTRACT']

        curMeta['url'] = collPath
        if 'extras' not in curMeta:
            curMeta['extras'] = []
        # TECHNICALINFO
        #if 'TECHNICALINFO' in metadata:
        #    curMeta['extras'].append({'key': 'iRODS ticket access with icommands', 'value': metadata['TECHNICALINFO']})
        # OTHER
        if 'OTHER' in metadata:
            curMeta['extras'].append({'key': 'Web access to iRODS instance', 'value': metadata['OTHER']})

        # collection iRODS path, PID and ticket --> otherId
        if 'PID' in metadata:
            curMeta['extras'].append({'key': 'Handle', 'value': 'hdl.handle.net/'+metadata['PID']})
        if 'TICKET' in metadata:
            curMeta['extras'].append({'key': 'Other ID', 'value': metadata['TICKET']})
 
        print curMeta
        #update CKAN entry
        action = 'package_update'
        action_url = 'http://{api}/action/{action}'.format(api=self.apiUrl, action=action)
        data_string = quote(json.dumps(curMeta))
        request = Request(action_url, data_string)
        request.add_header('Authorization', self.apiToken)    
        try:
            response = urlopen(request) # if name already exists or is not given throws 409
            self.data = curMeta
            errorMsg.append('CKAN PUBLISH INFO: Draft patched')
        except:
            errorMsg.append('CKAN PUBLISH ERROR: Draft not patched with with new metadata:' +
                'CREATOR, ABSTRACT, TECHNICALINFO, OTHER, PID or TICKET.')        
        return errorMsg

    def patchRefs(self, refs, prefix = 'hdl.handle.net/'):
        '''
        Patches a draft with tickets and pids for data objects as otherReferences.
        Expects a dictionary irods obj path --> ticket
        '''
        errorMsg = []
        curMeta = self.data
        if prefix == 'hdl.handle.net/':
            curMeta['extras'].append({'key': 'File Handles',
                'value': str([os.path.basename(ref)+'> '+prefix+refs[ref] for ref in refs])})
        else:
            curMeta['extras'].append({'key': 'iRODS ticket', 
                'value': str([ref+' '+prefix+refs[ref] for ref in refs])})

        action = 'package_update'
        action_url = 'http://{api}/action/{action}'.format(api=self.apiUrl, action=action)
        data_string = quote(json.dumps(curMeta))
        request = Request(action_url, data_string)
        request.add_header('Authorization', self.apiToken)

        try:
            response = urlopen(request) # if name already exists or is not given throws 409
            self.data = curMeta
            errorMsg.append('Dataverse PUBLISH INFO: Draft patched with refs: '+str(refs))
        except:
            errorMsg.append('Dataverse PUBLISH ERROR: Draft not patched with data references.')
        return errorMsg
