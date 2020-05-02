"""
@licence: Apache 2.0
@Copyright (c) 2018, Christine Staiger (SURFsara)
@author: Christine Staiger
@author: Stefan Wolfsheimer
"""

import os
import logging
import json
import uuid
from urllib2 import urlopen
from urllib2 import Request
from urllib2 import quote
from urllib2 import HTTPError
from iBridges.draft import Draft


class CkanDraft(Draft):
    argument_prefix = "ckan"

    @staticmethod
    def add_arguments(parser):
        fields = ['api_token', 'api_url', 'org', 'id', 'group']
        for i in fields:
            parser.add_argument('--ckan_' + i,
                                type=str)

    def __init__(self, api_token, api_url, org, id=None, group=''):
        self.logger = logging.getLogger('ipublish')
        self.apiToken = api_token
        self.apiUrl = api_url
        self.ckanOrg = org
        if id:
            self.ckanID = id
        else:
            self.ckanID = str(uuid.uuid1())
        self.group = group
        self.__dataset = None

    @property
    def uri(self):
        return self.apiUrl + "/" + self.ckanOrg

    @property
    def url(self):
        return self.apiUrl + "/" + self.ckanOrg

    @property
    def doi(self):
        return self.ckanID

    @property
    def repoName(self):
        return 'CKAN'

    @property
    def metaKeys(self):
        return ['TITLE', 'ABSTRACT', 'CREATOR']

    @property
    def hasData(self):
        return False

    def create(self, title):
        '''
        Create a draft in CKAN with some minimal metadata.
        '''
        action = "package_list"
        action_url = '{api}/action/{action}'.format(api=self.apiUrl,
                                                    action=action)
        self.logger.info('CkanDraft: Listing packages: %s', action_url)
        try:
            response = urlopen(action_url)
        except Exception as e:
            self.logger.error('urlopen %s: %s' % (action_url, str(e)))
            raise
        jsonstr = response.read()
        response_dict = json.loads(jsonstr)
        if self.ckanID in response_dict['result']:
            self.logger.warning("Draft already created: %s", self.ckanID)

        # create draft
        action = 'package_create'  # package_update
        action_url = '{api}/action/{action}'.format(api=self.apiUrl,
                                                    action=action)
        data = {'title': title,
                'owner_org': self.ckanOrg,
                'name': self.ckanID}
        if self.group != '':
            data['group'] = self.group
            data['groups'] = [{'name': self.group}]
        self.logger.info('CkanDraft: Request %s %s',
                         action_url,
                         json.dumps(data))
        self._action(action_url, data)
        fmt = '{api}/dataset/{id}'
        self.draftUrl = fmt.format(api=self.apiUrl.split('/api')[0],
                                   id=self.ckanID)
        self.__dataset = data

    def patch(self, metadata, collPath='irods'):
        '''
        Adds and updates metadata to a CKAN draft.
        Mandatory metadata entries: CREATOR, TITLE, ABSTRACT, SUBJECT
        If data is not uploaded it is advised to provide pids pointing
        to the data in iRODS or
        to provide tickets for anonym ous data download.
        NOTE: If the draft already contains files,
        the update of metadata will fail.
        Parameters:
        metadata = ipc.mdGet()
        collPath = iRODS path or webdav access to collection or data object
        '''
        curMeta = self.__dataset

        # CREATOR --> author
        curMeta['author'] = metadata['CREATOR']

        # ABSTRACT --> notes
        curMeta['notes'] = metadata['ABSTRACT']

        curMeta['url'] = collPath
        if 'extras' not in curMeta:
            curMeta['extras'] = []

        # OTHER
        if 'OTHER' in metadata:
            curMeta['extras'].append({'key': 'Web access to iRODS instance',
                                      'value': metadata['OTHER']})

        # collection iRODS path, PID and ticket --> otherId
        if 'PID' in metadata:
            prefix = 'hdl.handle.net/'
            curMeta['extras'].append({'key': 'Handle',
                                      'value': prefix + metadata['PID']})
        if 'TICKET' in metadata:
            curMeta['extras'].append({'key': 'Other ID',
                                      'value': metadata['TICKET']})
        action = 'package_update'
        action_url = '{api}/action/{action}'.format(api=self.apiUrl,
                                                    action=action)
        self._action(action_url, curMeta)
        self.__dataset = curMeta

    def patchTickets(self, tickets):
        self.patchRefs({'key': 'iRODS ticket',
                        'value': str([ref + ' Ticket: ' + value
                                      for ref, value in tickets.items()])})

    def patchPIDs(self, pids):
        prefix = 'hdl.handle.net/'
        self.patchRefs({'key': 'File Handles',
                        'value': str([os.path.basename(ref) +
                                      '> ' + prefix + value
                                      for ref, value in pids.items()])})

    def patchRefs(self, obj):
        '''
        Patches a draft with tickets and pids for data objects
        as otherReferences.
        Expects a dictionary irods obj path --> ticket
        '''
        curMeta = self.__dataset
        curMeta['extras'].append(obj)
        action = 'package_update'
        action_url = '{api}/action/{action}'.format(api=self.apiUrl,
                                                    action=action)
        self._action(action_url, curMeta)
        self.__dataset = curMeta

    def _action(self, action_url, data):
        try:
            data_string = quote(json.dumps(data))
            self.logger.debug('request %s', action_url)
            for line in json.dumps(data, indent=4).split('\n'):
                self.logger.debug(' %s', line)
            request = Request(action_url, data_string)
            request.add_header('Authorization', self.apiToken)
            urlopen(request)
            self.logger.info('CKAN PUBLISH INFO: Draft patched')
        except HTTPError as e:
            # if name already exists or is not given throws 409
            if e.code == 409:
                self.logger.warning('report already exists %s',
                                    json.dumps(data))
            else:
                self.logger.error('urlopen %s: %s' % (action_url, str(e)))
                raise
        except Exception as e:
            self.logger.error('urlopen %s: %s' % (action_url, str(e)))
            self.logger.error('CKAN PUBLISH:' +
                              'Draft not patched with with new metadata:' +
                              'CREATOR, ABSTRACT, TECHNICALINFO, ' +
                              'OTHER, PID or TICKET.')
            raise

    def publish(self):
        self.logger.info('publish draft %s', self.url)
