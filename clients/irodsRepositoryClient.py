from irods.access import iRODSAccess 

from b2handle.handleclient import EUDATHandleClient
from b2handle.clientcredentials import PIDClientCredentials

class irodsRepositoryClient():

    def __init__(self, irodspublishcoll, draft, pids = {}, tickets = {}, pidClient = ''):

        self.draft = draft
        self.ipc = irodspublishcoll
        print "Publish collection: ", self.ipc.coll.path
        print "Draft ID: ", self.draftId
        self.pids = pids
        self.tickets = tickets
        self.pidClient = picClient

    def checkCollection(pids = true, tickets = true):
        
        message = []
        #Check if flat directory and no DOI from repository (unpublished)
        message.extend(self.ipc.validate(repoKeys = [self.draft.repoName + '/DOI']))

        #Check if mandatory metadata is present
        if not set(ipc.mp.keys()).issubset(draft.metaKeys):
            message.append('REPOSITORY PUBLISH ERROR: Keys not defined: ' + str(set(draft.metaKeys).difference(ipc.md.keys()))

        #Create PIDs, if not done by eventhook in iRODS
        if pids and self.pids == {}:
            self.pids = ipc.assignPids(self.pidClient) 

        #Create tickets for anonymous download of data from iRODS, if data is not uploaded to repository
        if tickets and self.tickets == {}:
            self.tickets = ipc.assignTickets()

        return message

    def localCopyData(self, path = '/tmp'):
        '''
        Makes a local copy of the data files in the iRODS collection, used to upload to repository.
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

    def uploadToRepo(self, data=True):

        message = []
        message.extend(draft.patchGeneral(self.ipc.metadata))
        if tickets != {}:
            message.extend(draft.patchTickets(self.tickets))
        if tickets != {}:
            message.extend(draft.patchPIDs(self.pids))

        if data:
            folder = localCopyData()
            message.extend(uploadData(folder))        

        return message

    def addPublishIDtoIRODS(self, doi, id=''):
        '''
        Adds a PID from the repository to a collection in iRODS.
        key:    repoName/DOI: doi
                repoName/ID: id
        '''

        self.ipc.mdUpdate(draft.repoName+'/DOI', doi)
        if id != '':
            self.ipc.mdUpdate(draft.repoName+'/ID', self.draftId)

    def createReport(self, content, owners=[]):
        '''
        Creates a report file for the users in /zone/home/public.
        Naming convention: user1-user2-..._collection.status
        content - list of strings
        owners - iterable
        '''
        message = '\n'.join([str(i) for i in content])
        users   = '-'.join(owners)
        iPath   = '/'+self.ipc.session.zone+'/home/public/'+users+'_'+self.coll.name+'.status'

        try:
            obj = self.ipc.session.data_objects.create(iPath)
        except Exception:
            obj = self.session.data_object.get(iPath)
        with obj.open('w') as obj_desc:
            obj_desc.write(message)

        for user in owners:
            acl = iRODSAccess('write', iPath, user, self.session.zone)
            self.ipc.session.permissions.set(acl)
