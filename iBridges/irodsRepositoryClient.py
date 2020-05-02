import logging
import datetime
from irods.access import iRODSAccess


class iRodsRepositoryClient(object):

    def __init__(self, ipc, draft, pidClient=''):
        self.logger = logging.getLogger('ipublish')
        self.draft = draft
        self.ipc = ipc
        self.pids = ipc.getMDall('PID')
        self.tickets = ipc.getMDall('TICKET')
        self.pidClient = pidClient
        self.logger.info("Publish collection: %s", self.ipc.uri)
        self.logger.info("Draft Type: %s", self.draft.__class__.__name__)
        self.logger.info("Draft Url: %s", self.draft.uri)

    def getRepoKey(self, key):
        return self.draft.repoName + '/' + key

    def getRepoValue(self, key, default=None):
        return self.ipc.md.get(self.getRepoKey(key), default)

    def updateRepoValue(self, key, value):
        self.ipc.mdUpdate(self.getRepoKey(key), value)

    def isPublished(self):
        return self.ipc.isPublished([self.getRepoKey('DOI')])

    def checkCollection(self):
        # Check if flat directory and no DOI from repository (unpublished)
        ret = self.ipc.validate([self.getRepoKey('DOI')])

        # Check if mandatory metadata is present
        if not set(self.draft.metaKeys).issubset(self.ipc.md.keys()):
            self.logger.error('%s PUBLISH ERROR: Keys not defined: ',
                              self.draft.repoName)
            self.logger.error(' ' + str(set(self.draft.metaKeys).
                                        difference(self.ipc.md.keys())))
            ret = False
        else:
            self.logger.info('%s PUBLISH NOTE: all metadata defined:',
                             self.draft.repoName)
            self.logger.info(' ' + str(self.draft.metaKeys))

        return ret

    def assignSeriesInformation(self):
        self.ipc.assignSeriesInformation()

    # def assignPid(self):
    # @todo: check if we need pid creation
    # Create PIDs, if not present
    # if not self.pids:
    #    self.pids = self.ipc.assignPID(self.pidClient)
    #    self.logger.info('PIDs for collection: ', str(self.pids))
    # pass

    def assignTicket(self):
        # Create tickets for anonymous download of
        # data from iRODS if not present
        if not self.tickets:
            self.tickets, succ = self.ipc.assignTicket()
            if not succ:
                self.logger.error('Assigning tickets failed')
                raise RuntimeError('Assigning tickets failed')
        self.logger.info('Tickets for collection created:')
        for k, v in self.tickets.items():
            self.logger.info(' %s: %s', k, v)
        return self.tickets

    def patchDraft(self):
        if self.ipc.http:
            path = self.ipc.http + self.ipc.coll.path
        else:
            path = self.ipc.coll.path
        self.draft.patch(self.ipc.md, collPath=path)

    def patchDraftTickets(self):
        if self.tickets:
            self.draft.patchTickets(self.tickets)

    def patchDraftPIDs(self):
        if self.pids:
            self.draft.patchPIDs(self.pids)

    def uploadToRepo(self, remove=True):
        if self.draft.hasData:
            for obj in self.ipc.downloadCollection(remove=remove):
                self.draft.uploadFile(obj)
        else:
            self.logger.info('draft %s does not support data upload',
                             self.draft.__class__.__name__)

    def publishDraft(self):
        '''
        Publishes a draft (checks only on draft.draftUrl).
        Adds a PID from the repository to a collection in iRODS.
        key:    repoName/DOI: doi
                repoName/ID: id
        '''
        assert self.draft.url != ''
        self.draft.publish()
        self.updateRepoValue('DOI', self.draft.doi)
        self.updateRepoValue('URL', self.draft.url)

    def createDraft(self):
        return self.draft.create(self.ipc.title)

    def createReport(self, content, owners=[]):
        '''
        Creates a report file for the users in /zone/home/public.
        Naming convention: user1-user2-..._collection.status
        content - list of strings
        owners - iterable
        '''
        message = '\n'.join([str(i) for i in content])
        users = '-'.join(owners)
        iPath = '/%s/home/public/%s_%s.status_%s' % (
            self.ipc.session.zone, users, self.ipc.coll.name,
            datetime.datetime.now().strftime('%d-%m-%y_%H:%M'))
        self.logger.info('Create report %s', iPath)
        self.logger.debug('message:')
        for line in content:
            self.logger.debug(' ' + str(line))

        try:
            obj = self.ipc.session.data_objects.create(iPath)
        except Exception:
            obj = self.ipc.session.data_objects.get(iPath)
        with obj.open('w') as obj_desc:
            obj_desc.write(message)
        for user in owners:
            acl = iRODSAccess('write', iPath, user, self.ipc.session.zone)
            self.logger.debug('setting write permissions for user %s' % user)
            self.ipc.session.permissions.set(acl)

        return iPath

    def createReportNoRaise(self, content, owners=[]):
        try:
            self.createReport(content, owners)
        except Exception as e2:
            msg = str(e2)
            if not msg:
                msg = e2.__class__.__name__
            self.logger.critical(msg)
