import requests
import json
import time
import random
import os
import itertools
import traceback
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from initsocks.initsocks import SockSpin
from helper import batch_split, all_dirs, \
                all_files, get_filenames, make_dir, \
                check_make_dir, read_sort_filter_resave_keywords, \
                save_json, filterout_downloaded, get_numfiles, \
                parse_keyword, balance_check



import logging
logger = logging.getLogger(__name__)


class MultiThreadScraper:
    def __init__(self, socks_list, download_path, n_threads, keywords):
        self.socks_port_list = socks_list        
        
        self.n_threads = n_threads
        # self.pool = ThreadPoolExecutor(max_workers=n_threads)
        self.to_crawl = Queue()
        self.scraped_keywords = set([])
        self.search_url = "https://www.google.com/search?q={}&source=lnms&tbm=isch&safe=active"
        self.download_path = download_path

        self.keywords = keywords
        self.queue_up_list(self.keywords)
        
    def queue_up_list(self, keywords):
        for keyword in keywords:
            self.to_crawl.put(keyword)

    def parse_result(self, keyword, html):
        try:
            soup = BeautifulSoup(html, 'lxml')
            img_metadata_raw = [x.get_text() for x in soup.find_all('div', class_='rg_meta notranslate')]
            if len(img_metadata_raw) < 5:
                logger.warning('Result doesn\'t seem right, Quitting!')
                logger.warning('__________________\n{}\n{}\n____________________'.format(soup.title, img_metadata_raw))
                return None
            else:
                entry = {}
                entry['keyword'] = keyword
                entry['metadata'] = [json.loads(x) for x in img_metadata_raw]
                logger.info('_____________________\nGoogling done, Total: {}\n_____________________'.format(len(img_metadata_raw)))
                return entry
        except Exception as e:
            traceback.print_exc()
            return None

    def request_keyword(self, keyword):
        try:
            time.sleep(1)
            proxy = 'socks5://127.0.0.1:{}'.format(random.choice(self.socks_port_list))

            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
                            , 'Referer':'https://www.google.com'}
            url = self.search_url.format(keyword)
            rq = requests.get(url, headers=headers, proxies = {'http': proxy,'https': proxy}, timeout=3)
            print ("Requested {}".format(url))
            if rq.status_code == 200:
                parsed = self.parse_result(keyword, rq.text)
                save_json(download_dirpath=self.download_path, filename=keyword, data=parsed)
                print ("Saved {}".format(keyword))
                return rq
            else:
                return None
        except requests.RequestException as e:
            print ("ERROR request_keyword {}".format(keyword))
            print (e)
            return None

    def request_keyword_list(self, keyword_list):
        for keyword in keyword_list:
            self.request_keyword(keyword)


    def post_scrape_callback(self, res):
        result = res.result()
        if result and result.status_code == 200:
            print ("Success")

    def run_scraper(self):
        try:
            target_keyword = self.to_crawl.get(timeout=5)
            # print ("target_keyword : {}".format(target_keyword))
            if target_keyword not in self.scraped_keywords:
                self.scraped_keywords.add(target_keyword)
                job = self.pool.submit(self.request_keyword, target_keyword)
                # job.add_done_callback(self.post_scrape_callback)
        except Empty:
            return None
        except Exception as e:
            traceback.print_exc()

    def run_scraper_lazy(self):
        try:
            futures = []
            chunks = batch_split(self.keywords, 5000)
            with ThreadPoolExecutor(max_workers=self.n_threads) as pool_executor:
                for chunk in chunks:
                    pool_executor.submit(self.request_keyword_list, chunk)
        except Exception as e:
            traceback.print_exc()


if __name__ == '__main__':
    ssh_dump='KR_FRESH_12-25-2018_4937.txt'
    keyword_file='baomoi.com-organic-keywords-subdomains-VN-19-Jan-2019_combined.txt'
    keywords_filepath = os.path.join(os.getcwd(), keyword_file)
    download_dir='download'
    download_path = os.path.join(os.getcwd(), download_dir)
    check_make_dir(download_path)
    n_threads=20
    num_ssh = round(n_threads)
    sockspinner = SockSpin(ssh_dump_filename=ssh_dump, num_socks=num_ssh)
    ssh_list = sockspinner.spin_socks()
    # ssh_list = [10001, 10000]
    while not balance_check(download_dirpath=download_path, keywords_file_path=keywords_filepath):
        keywords = filterout_downloaded(download_path, keywords_filepath)
        scraper = MultiThreadScraper(ssh_list, download_path, n_threads, keywords)
        scraper.run_scraper_lazy()