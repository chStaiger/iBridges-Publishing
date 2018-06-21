#!/usr/bin/env python

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""
import json
import os

from dataverse import Connection
from dataverse.dataverse import Dataverse
from dataverse.dataset import Dataset

class dataverseDraft():

    def __init__(self, apiToken, apiUrl, alias, draftUrl = ''):
        self.apiToken   = apiToken
        self.apiUrl     = apiUrl
        self.alias  	= alias
        self.draftUrl   = draftUrl
        self.__dataset	= None
        self.repoName   = 'Dataverse'
        self.metaKeys   = ['TITLE', 'ABSTRACT', 'CREATOR', 'SUBJECT']

    def create(self, title):
        '''
        Create a draft in Dataverse with some minimal metadata.
        '''
        if self.draftUrl != '':
            print "Draft already created: " + self.draftUrl
            return ['Dataverse PUBLISH INFO: Draft already exists: ' + self.draftUrl] 
 
        connection = Connection(self.apiUrl, self.apiToken, use_https=False)
        dataverse = connection.get_dataverse(self.alias)

        #create draft
        #put some required default metadata
        creator='ibridges'
        description='Description'
        metadata = {'subject': 'Other'}
        try:
            self.__dataset = dataverse.create_dataset(title=title, creator=creator, 
                description=description, **metadata)
            self.__md = self.__dataset.get_metadata()
            self.draftUrl = 'http://'+self.__dataset.connection.host+'/dataset.xhtml?persistentId='+\
                self.__dataset.doi
            return 
        except:
            return ["Draft not created."] 

    def patchGeneral(self, metadata, collPath = 'irods'):
        '''
        Adds and updates metadata to a Datacite draft.
        Mandatory metadata entries: CREATOR, TITLE, ABSTRACT, SUBJECT
        If data is not uploaded it is advised to provide pids pointing to the data in iRODS or
        to provide tickets for anonym ous data download.
        NOTE: If the draft already contains files, the update of metadata will fail.
        Parameters:
        metadata = ipc.mdGet()
        collPath = iRODS path
        '''
        errorMsg = []
        curMeta = self.__dataset.get_metadata('latest')

        # CREATOR --> author
        old = self.search('author', curMeta['metadataBlocks']['citation']['fields'])
        new = old.copy()
        new['value'][0]['authorName']['value'] = metadata['CREATOR']
        idx = curMeta['metadataBlocks']['citation']['fields'].index(old)
        curMeta['metadataBlocks']['citation']['fields'][idx] = new

        # ABSTRACT --> dsDescription
        old = self.search('dsDescription', curMeta['metadataBlocks']['citation']['fields'])
        new = old.copy()
        new['value'][0]['dsDescriptionValue']['value'] = metadata['ABSTRACT']
        idx = curMeta['metadataBlocks']['citation']['fields'].index(old)
        curMeta['metadataBlocks']['citation']['fields'][idx] = new

        # TECHNICALINFO --> dataSources; new metadata
        if 'TECHNICALINFO' in metadata:
            new = {u'multiple': True,
               u'typeClass': u'primitive',
               u'typeName': u'dataSources',
               u'value': [u'Data source']}
            new['value'][0] = metadata['TECHNICALINFO']
            curMeta['metadataBlocks']['citation']['fields'].append(new)
      
        # OTHER --> alternativeURL
        if 'OTHER' in metadata:
            new = {u'multiple': False,
               u'typeClass': u'primitive',
               u'typeName': u'alternativeURL',
               u'value': u'http://myalturi.nl'}
            new['value'] = metadata['OTHER']
            curMeta['metadataBlocks']['citation']['fields'].append(new)

        # collection iRODS path, PID and ticket --> otherId
        new = self.addAltID('iRODS', collPath)
        curMeta['metadataBlocks']['citation']['fields'].append(new)

        if 'PID' in metadata:
            new = self.addAltID('Handle', 'hdl.handle.net/'+metadata['PID'])
            curMeta['metadataBlocks']['citation']['fields'].append(new)

        if 'TICKET' in metadata:
            new = self.addAltID('iRODS ticket', metadata['TICKET'])
            curMeta['metadataBlocks']['citation']['fields'].append(new)
 
        try:
            self.__dataset.update_metadata(curMeta)
            errorMsg.append('Dataverse PUBLISH INFO: Draft patched')
        except:
            errorMsg.append('Dataverse PUBLISH ERROR: Draft not patched with with new metadata: CREATOR, ABSTRACT, TECHNICALINFO, OTHER, PID or TICKET.')        
        return errorMsg

    def patchRefs(self, refs, prefix = 'hdl.handle.net/'):
        '''
        Patches a draft with tickets and pids for data objects as otherReferences.
        Expects a dictionary irods obj path --> ticket
        '''
        errorMsg = []
        curMeta = self.__dataset.get_metadata('latest')
        new = {u'multiple': True,
               u'typeClass': u'primitive',
               u'typeName': u'otherReferences',
               u'value': [u'Reference1', u'Reference2']}
        new['value'] = [os.path.basename(ref)+': '+prefix+refs[ref] for ref in refs]
        curMeta['metadataBlocks']['citation']['fields'].append(new)

        try:
            self.__dataset.update_metadata(curMeta)
            errorMsg.append('Dataverse PUBLISH INFO: Draft patched with refs: '+str(refs))
        except:
            errorMsg.append('Dataverse PUBLISH ERROR: Draft not patched with data references.')
        return errorMsg

    def uploadData(self, folder):
        '''
        Uploads local files from a folder to the draft.
        '''
        errorMsg = []

        uploadFiles = [folder +'/'+ fname for fname in os.listdir(folder)]
        try:
            self.__dataset.upload_filepaths(uploadFiles)
            errorMsg.append('Dataverse PUBLISH: Files uploaded')
        except:
             errorMsg.append('Dataverse PUBLISH ERROR: Files not uploaded ')
        return errorMsg

    def getDOI(self):
        return self.__dataset.doi

    def search(self, keyword, mdDictList):
        entries =  (element for element in mdDictList if element['typeName'] == keyword)
        try:
            entry = entries.next()
            return entry
        except:
            print keyword, 'does not exist in list.'
            return None

    def addAltID(self, IdAgency, IdValue):
        new = {u'multiple': True,
               u'typeClass': u'compound',
               u'typeName': u'otherId',
               u'value': [{u'otherIdAgency': {u'multiple': False,
               u'typeClass': u'primitive',
               u'typeName': u'otherIdAgency',
               u'value': u'Agency'},
               u'otherIdValue': {u'multiple': False,
               u'typeClass': u'primitive',
               u'typeName': u'otherIdValue',
               u'value': u'ID'}}]}
        new['value'][0]['otherIdAgency']['value'] = IdAgency
        new['value'][0]['otherIdValue']['value'] = IdValue
        return new

    def addReferences(self, refs):
        '''
        refs: Dictionary of path:pid or path:ticket.
        '''
        new = {u'multiple': True,
               u'typeClass': u'primitive',
               u'typeName': u'otherReferences',
               u'value': [u'Reference1', u'Reference2']}
        new['value'] = [os.path.basename(ref)+': '+refs[ref] for ref in refs]
        return new
