from irods.access import iRODSAccess 
import datetime
import shutil
import os

RED     = "\033[31m"
GREEN   = "\033[92m"
BLUE    = "\033[34m"
DEFAULT = "\033[0m"

class irodsRepositoryClient():

    def __init__(self, ipc, draft, pidClient = ''):

        self.draft = draft
        self.ipc = ipc
        print "Publish collection: ", ipc.coll.path
        print "Draft Url: ", self.draft.draftUrl
        self.pids = ipc.getMDall('PID')
        self.tickets = ipc.getMDall('TICKET')
        self.pidClient = pidClient

    def checkCollection(self, pids = True, tickets = True):
        
        message = []
        #Check if flat directory and no DOI from repository (unpublished)
        message.extend(self.ipc.validate(repoKeys = [self.draft.repoName + '/DOI']))

        #Check if mandatory metadata is present
        if not set(self.draft.metaKeys).issubset(self.ipc.md.keys()):
            message.append(self.draft.repoName + ' PUBLISH ERROR: Keys not defined: ')
            message.append(str(set(self.draft.metaKeys).difference(self.ipc.md.keys())))
        else:
            message.append(self.draft.repoName + ' PUBLISH NOTE: all metadata defined: ')
            message.append(str(self.draft.metaKeys))
                           
        #Create PIDs, if not present
        if pids and self.pids == {}:
            self.pids = self.ipc.assignPID(self.pidClient)
        message.extend(['PIDs for collection: ', str(self.pids)])

        #Create tickets for anonymous download of data from iRODS if not present
        if tickets and self.tickets == {}: 
            self.tickets, error = self.ipc.assignTicket()
            if error:
                message.extend(error)
                print RED + 'Assigning tickets failed' + DEFAULT
        message.extend(['Tickets for collection', str(self.tickets)])

        return message

    def localCopyData(self, path = '/tmp'):
        '''
        Makes a local copy of the data files in the iRODS collection, used to upload to repository.
        '''

        path = path + "/" + self.ipc.coll.name
        try:
            shutil.rmtree(path)
        except OSError:
            print path, "does not exist."
                           
        os.makedirs(path)

        for obj in self.ipc.coll.data_objects:
            buff = self.ipc.session.data_objects.open(obj.path, 'r').read()
            with open(path+'/'+obj.name, 'wb') as f:
                f.write(buff)

        return path

    def uploadToRepo(self, data=True):

        message = []
        #message.extend(self.draft.create(self.ipc.md['TITLE']))
        message.extend(self.draft.patchGeneral(self.ipc.md, collPath = self.ipc.coll.path))
        if self.tickets != {}:
            try:
                message.extend(self.draft.patchTickets(self.tickets))
            except:
                message.extend(self.draft.patchRefs(self.tickets, 'Ticket: '))
        if self.pids != {}:
            try:
                message.extend(self.draft.patchPIDs(self.pids))
            except:
                message.extend(self.draft.patchRefs(self.pids))
        if data:
            folder = self.localCopyData()
            message.extend(self.draft.uploadData(folder))        

        return message
                         
    def publishDraft(self):
        '''
        Publishes a draft (checks only on draft.draftUrl).
        Adds a PID from the repository to a collection in iRODS.
        key:    repoName/DOI: doi
                repoName/ID: id
        '''
        assert self.draft.draftUrl != ''
        
        message = []
        try: #B2SHARE
            doi = self.draft.publish()  
        except: #Dataverse
            doi = self.draft.getDOI() 
        message.append(self.ipc.mdUpdate(self.draft.repoName+'/DOI', doi))
        message.append(self.ipc.mdUpdate(self.draft.repoName+'/URL', self.draft.draftUrl))
                           
        return message                   

    def createReport(self, content, owners=[]):
        '''
        Creates a report file for the users in /zone/home/public.
        Naming convention: user1-user2-..._collection.status
        content - list of strings
        owners - iterable
        '''
        message = '\n'.join([str(i) for i in content])
        users   = '-'.join(owners)
        iPath   = '/'+self.ipc.session.zone+'/home/public/'+users+'_'+self.ipc.coll.name+'.status_'+datetime.datetime.now().strftime('%d-%m-%y_%H:%M')

        try:
            obj = self.ipc.session.data_objects.create(iPath)
        except Exception:
            obj = self.ipc.session.data_objects.get(iPath)
        with obj.open('w') as obj_desc:
            obj_desc.write(message)

        for user in owners:
            acl = iRODSAccess('write', iPath, user, self.ipc.session.zone)
            self.ipc.session.permissions.set(acl)
        
        return iPath
