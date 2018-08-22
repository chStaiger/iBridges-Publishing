import tempfile
import shutil
import logging


class Tempdir:
    def __init__(self, remove=True, **args):
        self.args = args
        self.remove = remove
        self.logger = logging.getLogger('ipublish')

    def __enter__(self):
        self.tmpdir = tempfile.mkdtemp(**self.args)
        self.logger.debug('Created temporary directory %s', self.tmpdir)
        return self.tmpdir

    def __exit__(self, type, value, traceback):
        if self.remove:
            self.logger.debug('Remove temporary directory %s', self.tmpdir)
            shutil.rmtree(self.tmpdir)

    @property
    def path(self):
        return str(self.tmpdir)


def buffered_read(file_object, chunk_size=1024):
    """
    Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data
