import itertools
import os
import json
from urllib.parse import parse_qsl
import traceback
import logging
logger = logging.getLogger(__name__)
# import pprint
# pp = pprint.PrettyPrinter(indent=3)

def batch_split(iterable, n_size):
    l = len(iterable)
    for ndx in range(0, l, n_size):
        yield iterable[ndx:min(ndx + n_size, l)]

def roundrobin(long, short):
    import itertools
    result = [[i,j] for i, j in zip(long, itertools.cycle(short))]
    return result
        # print('{} for {}'.format(i, j))


def all_dirs(path):
    paths = []
    for dir in os.listdir(path):
        if os.path.isdir(path + '/' + dir):
            paths.append(path + '/' + dir)
    return paths

def all_files(path):
    paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.isfile(path + '/' + file):
                paths.append(path + '/' + file)
    return paths

def get_filenames(path):
    """
    Get only filename without any extensions
    """
    filenames = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.isfile(path + '/' + file):
                filenames.append(os.path.splitext(file)[0])
    return filenames

def get_numfiles(path):
    import subprocess, ast
    num_files = subprocess.check_output('ls -1 {} | wc -l'.format(path), shell=True)
    return ast.literal_eval(num_files.decode('utf-8').strip())

def make_dir(dirname):
    current_path = os.getcwd()
    path = os.path.join(current_path, dirname)
    if not os.path.exists(path):
        os.makedirs(path)

def check_make_dir(path):
    # If download_path doesn't exist -> make one
    if not os.path.exists(path):
        os.mkdir(path)


def read_sort_filter_resave_keywords(downloaded_keywords, keywords_file_path):
    # read search keywords from file
    with open(keywords_file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        lines = text.split('\n')
        if '' in lines:
            lines.remove('')
        keywords = sorted(set(lines))

    
    exclude_downloaded = list(set(keywords)-set(downloaded_keywords))
    logger.warning('{} keywords found: '.format(len(keywords)))
    logger.warning('{} keywords downloaded/{} keywords in queue for crawling'\
            .format(len(downloaded_keywords), len(exclude_downloaded)))

    # re-save sorted keywords
    with open(keywords_file_path, 'w+', encoding='utf-8') as f:
        for keyword in keywords:
            f.write('{}\n'.format(keyword))

    return exclude_downloaded

def filterout_downloaded(download_dirpath, keywords_file_path):
    downloaded = get_filenames(download_dirpath)
    excluded = read_sort_filter_resave_keywords(downloaded_keywords=downloaded, keywords_file_path=keywords_file_path)
    return excluded

def save_json(download_dirpath, filename, data):
    try:
        download_dirpath = os.path.join(os.getcwd(), download_dirpath)
        output_path = '{}/{}.json'.format(download_dirpath, filename)
        if len(data['metadata']) > 10:
            with open(output_path, 'w', encoding='utf-8') as output_file:
                # print ('[DEBUG] Saving file named :  |||{}.json|||'.format(filename))
                # print (data)
                json.dump(data, output_file)
            logger.info('[DEBUG] Saved {}.json'.format(filename))
        else:
            logger.warning('Not saving anything, result doesn\'t seem right, path in this case : {}'.format(path))
    except OSError:
        logger.warning('OSERROR : ')
        traceback.print_exc()
        pass #fixme : dirty hacks
    except FileNotFoundError:
        logger.warning('FileNotFoundError : ')
        traceback.print_exc()
        pass




def balance_check(download_dirpath, keywords_file_path):
    """
    Returns True if number of downloaded keywords larger than THRESHOLD*(number of keywords)
    Returns False otherwise
    """
    KEYWORD_THRESHOLD = 0.90
    num_downloaded_files = get_numfiles(download_dirpath)
    with open(keywords_file_path, 'r', encoding='utf-8') as kw_file:
        num_keywords = len(list(kw_file.readlines()))
    logger.warning("Num_downloaded_files : {} / Num_keywords : {}".format(num_downloaded_files, num_keywords))
    if num_downloaded_files/num_keywords > KEYWORD_THRESHOLD:
        return True
    else:
        return False



def parse_keyword(url):
    try:
        p = parse_qsl(url)
        if 'search?q' in p[0][0]:
            return p[0][1]
        else:
            return None
    except Exception as e:
        print (e)
        pass