import logging
import copy

# iRODS imports
from irods.access import iRODSAccess


class NoOwnership(Exception):
    def __init__(self, message):
        super(NoOwnership, self).__init__(message)


class CollectionLock:
    def __init__(self, ipc):
        self.logger = logging.getLogger('ipublish')
        self.ipc = ipc
        self.original_acl = {}
        self.do_unlock = False

    def __enter__(self):
        self.lock()
        self.do_unlock = True

    def __exit__(self, type, value, traceback):
        if self.do_unlock:
            self.unlock()

    def check_ownership(self, user, obj_or_coll):
        if hasattr(obj_or_coll, 'owner_name') and \
           hasattr(obj_or_coll, 'owner_zone') and \
           obj_or_coll.owner_name == user.name and \
           obj_or_coll.owner_zone == user.zone:
            return True
        for acl in self.ipc.session.permissions.get(obj_or_coll):
            if acl.access_name == 'own' and \
               acl.user_name == user.name and \
               acl.user_zone == user.zone:
                return True
        return False

    def lock(self):
        self.logger.info('lock collection %s', self.ipc.uri)
        union = [self.ipc.coll] + self.ipc.coll.data_objects
        new_acls = self._lock_pass1(union)
        for acl in new_acls:
            self.logger.debug('set ACL: %s', vars(acl))
            self.ipc.session.permissions.set(acl)

    def unlock(self):
        user = self.ipc.user
        self.logger.info('unlock collection %s', self.ipc.uri)
        for (path, u), acl in self.original_acl.items():
            if acl.user_name != user.name or acl.user_zone != user.zone:
                self.logger.debug('set ACL: %s', vars(acl))
                self.ipc.session.permissions.set(acl)
        union = [self.ipc.coll] + self.ipc.coll.data_objects
        for ooc in union:
            for acl in self.ipc.session.permissions.get(ooc):
                if (acl.path, acl.user_name) not in self.original_acl:
                    racl = iRODSAccess('null',
                                       acl.path,
                                       acl.user_name,
                                       acl.user_zone)
                    self.logger.debug('set ACL: %s', vars(racl))
                    self.ipc.session.permissions.set(racl)

    def _lock_pass1(self, union):
        user = self.ipc.user
        new_acls = []
        for ooc in union:
            if not self.check_ownership(user, ooc):
                raise NoOwnership("current user (%s) is not owner of %s" %
                                  (user.name, ooc.path))
            self.logger.debug('backing up ACLs for %s' % ooc.path)
            new_acls.append(iRODSAccess('read',
                                        ooc.path,
                                        'public',
                                        user.zone))
            for acl in self.ipc.session.permissions.get(ooc):
                self.logger.debug('backup: %s', vars(acl))
                self.original_acl[(ooc.path, acl.user_name)] = copy.copy(acl)
                if acl.user_name != user.name or acl.user_zone != user.zone:
                    new_acls.append(iRODSAccess('read',
                                                acl.path,
                                                acl.user_name,
                                                acl.user_zone))
        return new_acls

    def finalize(self):
        self.do_unlock = True
