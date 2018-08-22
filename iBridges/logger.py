import logging
from termcolor import colored
try:
    # Python 2
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


def format_error(st):
    return colored(st, color='red', attrs=['bold'])


def format_question(st):
    return colored(st, color='green', attrs=['bold'])


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color
        self.colormap = {
            'DEBUG': {'color': 'grey', 'attrs': ['bold']},
            'INFO': {'color': 'green'},
            'WARN': {'color': 'yellow', 'attrs': ['bold']},
            'WARNING': {'color': 'yellow', 'attrs': ['bold']},
            'ERROR': {'color': 'red'},
            'CRITICAL': {'color': 'red', 'attrs': ['bold']}}

    def format(self, record):
        s = logging.Formatter.format(self, record)
        if self.use_color and record.levelname in self.colormap:
            return colored(s, **self.colormap[record.levelname])
        else:
            return s


class LoggerFactory(object):
    def __init__(self, verbose=False, colored=True):
        if verbose:
            fmt = '%(asctime)s %(levelname)-8s ' + \
                  '%(pathname)s:%(lineno)d %(message)s'
        else:
            fmt = '%(asctime)s %(levelname)-8s %(message)s'
        self.logger = logging.getLogger('ipublish')
        self.log_stream = StringIO()
        stream_handler = logging.StreamHandler()
        string_handler = logging.StreamHandler(self.log_stream)
        stream_handler.setFormatter(ColoredFormatter(fmt, colored))
        stream_handler.setLevel(logging.DEBUG)
        string_handler.setFormatter(logging.Formatter(fmt))
        string_handler.setLevel(logging.WARNING)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(string_handler)
        self.logger.setLevel(logging.DEBUG)

    def get_logger(self):
        return self.logger

    def get_logs(self):
        return self.log_stream.getvalue().split('\n')
