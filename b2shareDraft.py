!/usr/bin/env python

"""
@licence: Apache 2.0
@Copyright (c) 2017, Christine Staiger (SURFsara)
@author: Christine Staiger
"""

#B2SHARE imports
import requests
import json

class B2SHAREdraft():

    def __init__(self, apiToken, apiUrl, communityId, draftUrl = ‘’):
        self.apiToken   = apiToken
        self.apiUrl     = apiUrl
        self.community  = communityId
        self.draftUrl   = draftUrl
        self.repoName   = ‘B2SHARE’
        self.metaKeys   = [‘CREATOR’, ‘TITLE’, ‘TABLEOFCONTENTS’, ‘SERIESINFORMATION’, ‘TECHNICALINFO’]


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

    def patchGeneral(metadata):
        '''
        Adds metadata to a B2SHARE draft.
        Mandatory metadata entries: CREATOR, TITLE
        If data is not uploaded it is advised to provide pids pointing to the data in iRODS or
        to provide tickets for anonym ous data download.
        '''
        errorMsg = []
        headers = {"Content-Type":"application/json-patch+json"}

        # CREATOR
        patch = '[{"op":"add","path":"/creators","value":[{"creator_name":"' + \
            metadata['CREATOR'] + '"}]}]'
        response = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        if response.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with creators. ' + \
            str(request.status_code))
        print "added creator"

        #DESCRIPTION: ABSTRACT, TOC, SERIESINFO, TECHNICALINFO
        #NOTE: metadata['TECHNICALINFO']=
        #'irods_host alice-centos; irods_port 1247; irods_user_name anonymous;
        #irods_zone_name aliceZone;
        #iget/ils -t <ticket> /aliceZone/home/public/b2share/myDeposit'
        patch = '[{"op":"add","path":"/descriptions","value":[{"description":"'+ metadata['ABSTRACT'] + \
            '", "description_type":"Abstract"},{"description":"'+metadata['SERIESINFORMATION'] + \
            '", "description_type":"SeriesInformation"}, {"description":"Ticket: '+metadata['TABLEOFCONTENTS'] + \
            '", "description_type":"TableOfContents"},{"description":"'+metadata['TECHNICALINFO'] + \
            '", "description_type":"TechnicalInfo"}]}]'
        response = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        if response.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with description. ' + \
            str(response.status_code))
        print "added description"

        return errorMsg

    def patchTickets(self, tickets):
        '''
        Patches a draft with tickets as Resource Type.
        Expects a dictionary irods obj oath --> ticket
        '''
        tmp = []
        for ticket in tickets:
        tmp.append('{"resource_type": "path='+ticket+' ticket='+tickets[ticket]+\
            '", "resource_type_general": "Dataset"}')
        patch = '[{"op":"add","path":"/resource_types","value":[' + ','.join(tmp)+']}]'
        request = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with tickets. ' + str(request.status_code))

        return errorMsg

    def patchPIDs(self, pids):
        '''
        Patches a draft with PIDs as alternmate identifiers.
        Expects a diuctionary irods obj name --> pids
        '''
        tmp = []
        for pid in pids:
            tmp.append('{"alternate_identifier": "'+pids[pid]+\
                '", "alternate_identifier_type": "EPIC;'+\
                pid+'"}')
        patch = '[{"op":"add","path":"/alternate_identifiers","value":[' + ','.join(tmp)+']}]'
        request = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with pids. ' + str(request.status_code))

        return errorMsg

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
