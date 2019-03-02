from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException
import platform
import time
import traceback
import logging
logger = logging.getLogger(__name__)

class TrafficBooster:
    def __init__(self):
        executable = ''

        if platform.system() == 'Windows':
            print('Detected OS : Windows')
            executable = './chromedriver/chromedriver_win.exe'
        elif platform.system() == 'Linux':
            print('Detected OS : Linux')
            executable = './chromedriver/chromedriver_linux'
        elif platform.system() == 'Darwin':
            print('Detected OS : Darwin')
            executable = './chromedriver/chromedriver_mac'
        else:
            assert False, 'Unknown OS Type'

        self.executable = executable

    def boost(self, url, ssh_local_port, sleep=30):
        # Setting Chrome Options then start the browser session
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('headless')
        # set the window size
        chrome_options.add_argument('window-size=1200x600')
        # chrome_options.add_argument('disable-gpu')
        chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:{}'.format(ssh_local_port))
        chrome_options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"')
        self.browser = webdriver.Chrome(executable_path=self.executable, options=chrome_options)

        try:
            self.browser.get(url)
            time.sleep(sleep) #Sleep 'sleep' seconds before closing browser
            self.browser.close()
            logger.info('Successfully accessed {} on proxy running on port {}'.format(url, ssh_local_port))
        except:
            traceback.print_exc()
            logger.warning('Could not access {} on proxy running on {}'.format(url, ssh_local_port))
            pass