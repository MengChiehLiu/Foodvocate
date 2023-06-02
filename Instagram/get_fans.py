'''
Foodvocate: Instagram scraping - get fans
Author: Meng-Chieh Liu
Github: https://github.com/MengChiehLiu
Date: 2023/5/22
'''

import requests
from dotenv import load_dotenv
import os
import pandas as pd
from queue import Queue
from utils.runThreading import runThreading
from threading import Lock
import logging
import random
import time

# log settings
logging.basicConfig(level=logging.INFO)

# check and create directory
if not os.path.isdir('data'):
    os.mkdir('data')
if not os.path.isdir('data/posts'):
    os.mkdir('data/posts')

# Before use it, update environment variables first.
load_dotenv()
SESSION = os.environ['SESSION']
CSRF = os.environ['CSRF']
cookies = {
    'csrftoken': CSRF,
    'sessionid': SESSION
}

# request headers
headers = {
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-full-version-list': '"Chromium";v="112.0.5615.138", "Google Chrome";v="112.0.5615.138", "Not:A-Brand";v="99.0.0.0"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-csrftoken': CSRF,
    'x-ig-app-id': '936619743392459',
    'x-requested-with': 'XMLHttpRequest'
}


def get_fans(username):
    try:
        logging.info("Good!")
        time.sleep(random.uniform(1, 4)) # adjustable time gap
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        response = requests.get(url=url, headers=headers, cookies=cookies).json()
        fans = response['data']['user']['edge_followed_by']['count']
        bloggers_lock.acquire() # enhance thread safety
        bloggers[username] = fans
        bloggers_lock.release() # enhance thread safety
    except:
        logging.info("Error!")


if __name__ == "__main__":
    bloggers_lock = Lock() # enhance thread safety
    my_queue = Queue()

    # check state: continue/new
    if os.path.exists('data/bloggers_with_fans.csv'):
        bloggers_df = pd.read_csv('data/bloggers_with_fans.csv', index_col='Unnamed: 0')
        bloggers = bloggers_df['fans'][bloggers_df['fans'].notna()].map(int).to_dict()
        bloggers_na = bloggers_df['fans'][bloggers_df['fans'].isna()].index
        bloggers_df = bloggers_df.drop('fans', axis=1)
        for blogger in bloggers_na:
            my_queue.put(blogger)
    else:
        bloggers_df = pd.read_csv('data/bloggers.csv', index_col='Unnamed: 0')
        bloggers = {}
        for blogger in bloggers_df.index:
            my_queue.put(blogger)
    
    # (multi-thread) get fans
    logging.info("Start running!")
    runThreading(my_queue, get_fans, 2) # 2 is the thread amount, reduce it to prevent being blocked :(
    
    # save blogger df
    fans = pd.DataFrame.from_dict(bloggers, orient='index', columns=['fans'])
    new_bloggers_df = pd.merge(bloggers_df, fans, left_index=True, right_index=True, how='outer')
    new_bloggers_df.to_csv('data/bloggers_with_fans.csv')
    logging.info("Finish all!")