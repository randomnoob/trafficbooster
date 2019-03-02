from engine import TrafficBooster
from initsocks.initsocks import SockSpin
from multiprocessing import Pool
import random

import logging
logger = logging.getLogger(__name__)

GLOBAL_SSH_DUMP = 'KR_FRESH_12-25-2018_4937.txt'


class MultithreadedBooster:
    def __init__(self, url, num_proxies, num_threads):
        """
        Chạy bao giờ hết số num_proxies thì thôi
        num_threads là số thread chạy đồng thời
        """
        self.url = url
        self.num_threads = num_threads
        # Tạo mới số lượng proxy bằng với số threads +3
        sockspinner = SockSpin(
            ssh_dump_filename=GLOBAL_SSH_DUMP, num_socks=num_proxies)
        self.proxy_port_list = sockspinner.spin_socks()

    def run_booster_process(self, proxy):
        booster = TrafficBooster()
        booster.boost(url=self.url, ssh_local_port=proxy, sleep=40)

    def run(self):
        process_pool = Pool(self.num_threads)
        process_pool.map(self.run_booster_process, self.proxy_port_list)
        process_pool.close()
        process_pool.join()
        print('pool join')
        print('End Program')


if __name__ == '__main__':
    MultithreadedBooster(url='http://watergovernancecentre.nl', num_threads=2, num_proxies=30).run()
