from .core import pxssh
import traceback
import subprocess
import requests
import time
import os
import stat
import random

LIMIT_NUM_SOCKS = 40
SSHPASS_CMD_TEMPLATE = 'sshpass -p {password} nohup ssh -D {port} -M -S {socket} -f -q -N -C {username}@{host}'

class SockSpin:
    def __init__(self, ssh_dump_filename, num_socks, encoding='utf-8'):
        with open(ssh_dump_filename, encoding=encoding) as dump:
            ssh_strings = [x.strip() for x in dump.readlines()]
            ssh = [x.split('|')[:3] for x in ssh_strings]
            random.shuffle(ssh)
            self.ssh = ssh
            print ('SOCKS list loaded and shuffled')
        self.num_socks = num_socks
        self.cwd = os.getcwd()
        self.base_port = 9001

    def check_ifsocket(self, path, tries=3, wait=0):
        try:
            if wait:
                time.sleep(1)
            mode = os.stat(path).st_mode
            return stat.S_ISSOCK(mode)
        except FileNotFoundError:
            if tries==0:
                return False
            else:
                print ('Wait 1 sec and check socket_filepath again')
                return self.check_ifsocket(path, tries=tries-1, wait=1)

    @staticmethod
    def try_login(host, username, password):
        try:
            logfile=open(os.path.join(os.getcwd(), "SOCKSPIN.log"), "w")
            p = pxssh(logfile=logfile, encoding='utf-8', timeout=10)
            p.login(host, username, password, login_timeout=4)
            return True
        except Exception as err:
            print("Exception : {0}".format(err))
            # traceback.print_exc()
            return False

    def forkspin(self, host, username, password, port):
        """
        Spin up an SSH session with -M "master" mode and a -S "socket" included, using sshpass
        to pass the password as plain text, enabling the ability to start unattended ssh sessions
        Then checks if "socket" exists. If it does, then return True, meaning socks5 established

        eg sshpass -p passwordishere nohup ssh -D 9001 -M -S ~/.ssh/9001.sock -C -N -f bamboo@chicken.thitgaluoc.com
        the NOHUP is for single-core machines which slows down the forking process of ssh, therefore cause it to close down
        because of SIGHUP signal from the os.
        """
        try:
            login_attempt = self.try_login(host, username, password)
            if login_attempt:
                # Socket path set to current working dir
                socket_dirpath = os.path.join(self.cwd, 'socket')
                socket_filepath = os.path.join(socket_dirpath, '{}.sock'.format(port))
                if not os.path.exists(socket_dirpath):
                    os.mkdir(socket_dirpath)
                # SSHPASS comes to the rescue
                cmd = SSHPASS_CMD_TEMPLATE.format(username=username, password=password, port=port, host=host, socket=socket_filepath)
                print ('____________________________________________________________________________\n{}'.format(cmd))
                # Spawn SSHPASS
                p = subprocess.Popen(cmd, shell=True)
                print ("Spawned 127.0.0.1:{}".format(port))
                # Checks if socket_filepath actually exists
                # Wait 1 seconds for the socket to initialize
                time.sleep(1)
                if self.check_ifsocket(socket_filepath):
                    print ('Socket file FOUND')
                    return True
                else:
                    print ('Socket file doesn\'t exist. Bypassing')
                    return False
            else:
                print ('Connection failed')
                return False
            print ('____________________________________________________________________________')
        except Exception as err:
            print("Exception : {0}".format(err))
            traceback.print_exc()
            return False

    def request_through_socks(self, port, host, tries=3):
        try:
            if tries==0:
                return False
            proxy = 'socks5://127.0.0.1:{}'.format(port)
            print ('Testing with : ', proxy)
            r = requests.get('http://icanhazip.com', proxies = {
                                                                'http': proxy,
                                                                'https': proxy
                                                                }, timeout=8)
            if r.status_code == 200:
                return True
            else:
                return self.request_through_socks(port, host, tries=tries-1)
        except ConnectionError as err:
            print ('ConnectionError : {}'.format(err))
            print ('Retrying 3 times')
            return self.check_socks_connect(port, host, tries=tries-1)
        except ConnectionRefusedError as err:
            print ('ConnectionRefusedError')
            return False
        except:
            traceback.print_exc()
            return False

    def google_through_socks(self, port, host, tries=3):
        try:
            if tries==0:
                return False
            proxy = 'socks5://127.0.0.1:{}'.format(port)
            print ('Testing with : ', proxy)
            r = requests.get('https://www.google.com/search?client=ubuntu&channel=fs&q=sfgvdf+&ie=utf-8&oe=utf-8', proxies = {
                                                                'http': proxy,
                                                                'https': proxy
                                                                }, timeout=8)
            if r.status_code == 200:
                if not 'unusual traffic from your computer network' in r.text:
                    return True
                else:
                    return False
            else:
                return self.request_through_socks(port, host, tries=tries-1)
        except ConnectionError as err:
            print ('ConnectionError : {}'.format(err))
            print ('Retrying 3 times')
            return self.check_socks_connect(port, host, tries=tries-1)
        except ConnectionRefusedError as err:
            print ('ConnectionRefusedError')
            return False
        except:
            traceback.print_exc()
            return False


    def spin_socks(self):
        result = []
        for plus_port, test in enumerate(self.ssh):
            local_port = self.base_port+plus_port
            host = test[0]
            username = test[1]
            password = test[2]
            spinafork = self.forkspin(host, username, password, local_port)
            if spinafork:
                print ('Sleeping 1 seconds before checking with requetss')
                time.sleep(1)
                sock_request = self.request_through_socks(local_port, host)
                print ('REQUEST THROUGH SOCKS5 : {}'.format(sock_request))
                if sock_request:
                    sock_google = self.google_through_socks(local_port, host)
                    print ('GOOGLE THROUGH SOCKS5 : {}'.format(sock_google))
                    if sock_google:
                        result.append(local_port)
                        print ('+++++++++GOT ===>{}<=== SOCKS++++++++\n{}____________________________'.format(len(result), result))
            if len(result) >= self.num_socks:
                break

        result = [str(x) for x in result]
        print ('RESULT : {}'.format(result))
        return result

# c = SockSpin(ssh_dump_filename='INTER_FRESH_12-21-2018_3429.txt', num_socks=5, encoding="ISO-8859-1")
# d = c.spin_socks()
# print (d)


# with open('INTER_FRESH_12-21-2018_3429.txt', encoding = "ISO-8859-1") as ssh_dump:
#     info = [x.strip() for x in ssh_dump.readlines()]
#     info_args = [x.split('|')[:3] for x in info]
#     random.shuffle(info_args)
#     print ('SOCKS list loaded and shuffled')

# def check_ifsocket(path, tries=3, wait=0):
#     try:
#         if wait:
#             time.sleep(1)
#         mode = os.stat(path).st_mode
#         return stat.S_ISSOCK(mode)
#     except FileNotFoundError:
#         if tries==0:
#             return False
#         else:
#             print ('Wait 1 sec and check socket_filepath again')
#             return check_ifsocket(path, tries=tries-1, wait=1)

# def try_login(host, username, password):
#     try:
#         logfile=open("/home/nl/dev/sshconn/mylog.txt", "w")
#         p = pxssh(logfile=logfile, encoding='utf-8', timeout=10)
#         p.login(host, username, password, login_timeout=4)
#         return True
#     except Exception as err:
#         print("Exception : {0}".format(err))
#         traceback.print_exc()
#         return False
# def forkspin(host, username, password, port):
#     """
#     Spin up an SSH session with -M "master" mode and a -S "socket" included, using sshpass
#     to pass the password as plain text, enabling the ability to start unattended ssh sessions
#     Then checks if "socket" exists. If it does, then return True, meaning socks5 established

#     eg sshpass -p passwordishere ssh -D 9001 -M -S ~/.ssh/9001.sock -C -N -f bamboo@chicken.thitgaluoc.com
#     """
#     try:
#         login_attempt = try_login(host, username, password)
#         if login_attempt:
#             logfile=open("/home/nl/dev/sshconn/mylog.txt", "w")
#             # Socket path set to current working dir
#             socket_filepath = os.path.join(os.getcwd(), 'socket/{}.sock'.format(port))
#             # SSHPASS comes to the rescue
#             cmd_template= 'sshpass -p {password} ssh -D {port} -M -S {socket} -f -q -N -C {username}@{host}'
#             cmd = cmd_template.format(username=username, password=password, port=port, host=host, socket=socket_filepath)
#             print ('____________________________________________________________________________')
#             print (cmd)
#             # Spawn SSHPASS
#             p = subprocess.Popen(cmd, shell=True)
#             print ("Spawned {}".format(port))
#             # Checks if socket_filepath actually exists
#             # Wait 1 seconds for the socket to initialize
#             time.sleep(1)
#             if check_ifsocket(socket_filepath):
#                 print ('Socket file FOUND')
#                 return True
#             else:
#                 print ('Socket file doesn\'t exist. Bypassing')
#                 return False
#         else:
#             print ('Connection failed')
#             return False
#         print ('____________________________________________________________________________')
#     except Exception as err:
#         print("Exception : {0}".format(err))
#         traceback.print_exc()
#         return False

# def request_through_socks(port, host, tries=3):
#     try:
#         if tries==0:
#             return False
#         proxy = 'socks5://127.0.0.1:{}'.format(port)
#         print ('Testing with : ', proxy)
#         r = requests.get('http://icanhazip.com', proxies = {
#                                                             'http': proxy,
#                                                             'https': proxy
#                                                             })
#         if r.status_code == 200:
#             return True
#         else:
#             return request_through_socks(port, host, tries=tries-1)
#     except ConnectionError as err:
#         print ('ConnectionError : {}'.format(err))
#         print ('Retrying 3 times')
#         return check_socks_connect(port, host, tries=tries-1)
#     except ConnectionRefusedError as err:
#         print ('ConnectionRefusedError')
#         return False
#     except:
#         traceback.print_exc()
#         return False

# def google_through_socks(port, host, tries=3):
#     try:
#         if tries==0:
#             return False
#         proxy = 'socks5://127.0.0.1:{}'.format(port)
#         print ('Testing with : ', proxy)
#         r = requests.get('https://www.google.com/search?client=ubuntu&channel=fs&q=sfgvdf+&ie=utf-8&oe=utf-8', proxies = {
#                                                             'http': proxy,
#                                                             'https': proxy
#                                                             })
#         if r.status_code == 200:
#             if not 'unusual traffic from your computer network' in r.text:
#                 return True
#             else:
#                 return False
#         else:
#             return request_through_socks(port, host, tries=tries-1)
#     except ConnectionError as err:
#         print ('ConnectionError : {}'.format(err))
#         print ('Retrying 3 times')
#         return check_socks_connect(port, host, tries=tries-1)
#     except ConnectionRefusedError as err:
#         print ('ConnectionRefusedError')
#         return False
#     except:
#         traceback.print_exc()
#         return False


# def get_socks(base_port):
#     result = []
#     for plus_port, test in enumerate(info_args):
#         local_port = base_port+plus_port
#         host = test[0]
#         username = test[1]
#         password = test[2]
#         spinafork = forkspin(host, username, password, local_port)
#         if spinafork:
#             print ('Sleeping 1 seconds before checking with requetss')
#             time.sleep(1)
#             sock_request = request_through_socks(local_port, host)
#             print ('REQUEST THROUGH SOCKS5 : {}'.format(sock_request))
#             if sock_request:
#                 sock_google = google_through_socks(local_port, host)
#                 print ('GOOGLE THROUGH SOCKS5 : {}'.format(sock_google))
#                 if sock_google:
#                     result.append(local_port)
#                     print ('+++++++++GOT     {}       SOCKS++++++++\n{}____________________________'.format(len(result), result))
#         if len(result) > LIMIT_NUM_SOCKS:
#             break

#     result = [str(x) for x in result]
#     print (result)
#     return result



# get_socks(9001)