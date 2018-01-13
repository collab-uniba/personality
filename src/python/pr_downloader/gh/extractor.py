
import datetime
from math import ceil
from multiprocessing import current_process
from time import sleep
import logging


class BaseGitHubThreadedExtractor(object):
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    tokens = None
    tokens_queue = None
    pid = None
    tokens_map = None
    seen = None

    def __init__(self, _tokens, t_queue, t_map):
        self.tokens = _tokens
        self.tokens_queue = t_queue
        self.tokens_map = t_map
        self.seen = set()

    def initialize(self):
        self.pid = current_process().pid
        self.tokens_map[self.pid] = self.tokens_queue.get()

    @staticmethod
    def get_rate_limit(g):
        return g.rate_limiting

    @staticmethod
    def compute_sleep_duration(g):
        reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
        curr_time = datetime.datetime.now()
        return abs(int(ceil((reset_time - curr_time).total_seconds())))

    @staticmethod
    def wait_if_depleted(pid, g):
        (remaining, _limit) = BaseGitHubThreadedExtractor.get_rate_limit(g)
        sleep_duration = BaseGitHubThreadedExtractor.compute_sleep_duration(g)
        if not remaining > 5:
            BaseGitHubThreadedExtractor.log.info(
                "[pid: {0}] Process depleted, going to sleep for {1} min.".format(pid, int(sleep_duration / 60)))
            sleep(sleep_duration)
