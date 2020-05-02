#!/usr/bin/env python
"""
@licence: Apache 2.0
@Copyright (c) 2017-2018, Christine Staiger (SURFsara)
@author: Christine Staiger
@author: Stefan Wolfsheimer
"""

import os
import logging
from iBridges.draft import Draft
from dataverse import Connection


class DataverseDraft(Draft):
    argument_prefix = "dataverse"

    @staticmethod
    def add_arguments(parser):
        for i in ['api_token', 'api_url', 'community', 'draft_url']:
            parser.add_argument('--dataverse_' + i,
                                type=str)

    def __init__(self, api_token, api_url, community, draft_url=''):
        self.logger = logging.getLogger('ipublish')
        self.apiToken = api_token
        self.apiUrl = api_url
        self.alias = community
        self.draftUrl = draft_url
        self.__dataset = None

    @property
    def uri(self):
        return self.apiUrl + "/" + self.alias

    @property
    def doi(self):
        return self.__dataset.doi

    @property
    def url(self):
        return self.draftUrl

    @property
    def repoName(self):
        return 'Dataverse'

    @property
    def metaKeys(self):
        return ['TITLE', 'ABSTRACT', 'CREATOR', 'SUBJECT']

    @property
    def hasData(self):
        return True

    def create(self, title):
        '''
        Create a draft in Dataverse with some minimal metadata.
        '''
        if self.draftUrl != '':
            raise RuntimeError("Dataverse PUBLISH:" +
                               "Draft already created: " + self.draftUrl)

        self.logger.debug('connect to %s', self.apiUrl)
        connection = Connection(self.apiUrl, self.apiToken, use_https=False)
        dataverse = connection.get_dataverse(self.alias)

        # create draft
        # put some required default metadata
        creator = 'ibridges'
        description = 'Description'
        metadata = {'subject': 'Other'}
        self.logger.info('create draft title=%s, creator=%s, description=%s' %
                         (title, creator, description))
        self.__dataset = dataverse.create_dataset(title=title,
                                                  creator=creator,
                                                  description=description,
                                                  **metadata)
        self.__md = self.__dataset.get_metadata()
        self.draftUrl = 'http://' + self.__dataset.connection.host + \
                        '/dataset.xhtml?persistentId=' + \
                        self.__dataset.doi
        self.logger.info('draft created: %s', self.draftUrl)

    def patch(self, metadata, collPath='irods'):
        '''
        Adds and updates metadata to a Datacite draft.
        Mandatory metadata entries: CREATOR, TITLE, ABSTRACT, SUBJECT
        If data is not uploaded it is advised to provide pids pointing to
        the data in iRODS or to provide tickets for anonym ous data download.
        NOTE: If the draft already contains files,
        the update of metadata will fail.
        Parameters:
        metadata = ipc.mdGet()
        collPath = iRODS path
        '''
        curMeta = self.__dataset.get_metadata('latest')

        # CREATOR --> author
        old = self.search('author',
                          curMeta['metadataBlocks']['citation']['fields'])
        new = old.copy()
        new['value'][0]['authorName']['value'] = metadata['CREATOR']
        idx = curMeta['metadataBlocks']['citation']['fields'].index(old)
        curMeta['metadataBlocks']['citation']['fields'][idx] = new

        # ABSTRACT --> dsDescription
        old = self.search('dsDescription',
                          curMeta['metadataBlocks']['citation']['fields'])
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
            self.logger.info('Dataverse PUBLISH INFO: Draft patched')
        except Exception:
            self.logger.error('Dataverse PUBLISH ERROR:' +
                              'Draft not patched with with new metadata')
            self.logger.error('CREATOR, ABSTRACT, TECHNICALINFO, OTHER, PID ' +
                              'or TICKET.')
            raise

    def patchTickets(self, tickets):
        self.patchRefs(tickets, 'Ticket: ')

    def patchPIDs(self, pids):
        self.patchRefs(pids)

    def patchRefs(self, refs, prefix='hdl.handle.net/'):
        '''
        Patches a draft with tickets and
        pids for data objects as otherReferences.
        Expects a dictionary irods obj path --> ticket
        '''
        curMeta = self.__dataset.get_metadata('latest')
        new = {u'multiple': True,
               u'typeClass': u'primitive',
               u'typeName': u'otherReferences',
               u'value': [u'Reference1', u'Reference2']}
        new['value'] = [os.path.basename(ref)+': '+prefix+refs[ref]
                        for ref in refs]
        curMeta['metadataBlocks']['citation']['fields'].append(new)

        try:
            self.__dataset.update_metadata(curMeta)
            self.logger.info('Dataverse PUBLISH: Draft patched with refs: %s',
                             str(refs))
        except Exception as e:
            msg = str(e)
            if not msg:
                msg = e.__class__.__name__
            self.logger.error('Dataverse PUBLISH ERROR:' +
                              'Draft not patched with data references: %s.',
                              msg)
            raise

    def uploadFile(self, path):
        self.logger.debug('upload file %s', path)
        self.__dataset.upload_filepath(path)

    def publish(self):
        self.logger.info('publish draft %s', self.url)

    def search(self, keyword, mdDictList):
        entries = (element for element in mdDictList
                   if element['typeName'] == keyword)
        try:
            entry = entries.next()
            return entry
        except Exception:
            self.logger.warning('%s does not exist in list.',
                                keyword)
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
