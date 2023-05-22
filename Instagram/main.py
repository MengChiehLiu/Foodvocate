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

logging.basicConfig(level=logging.INFO)

if not os.path.isdir('data'):
    os.mkdir('data')
if not os.path.isdir('data/posts'):
    os.mkdir('data/posts')

load_dotenv()
SESSION = os.environ['SESSION']
CSRF = os.environ['CSRF']
cookies = {
    'csrftoken': CSRF,
    'sessionid': SESSION
}

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


def read_location_ids(path):
    # check file type
    extension = path.split('.')[-1]
    if extension == 'xlsx':
        df = pd.read_excel(path)
    elif extension == 'csv':
        df = pd.read_csv(path)
    else:
        raise ValueError("file path should be excel or csv.")

    location_ids = set(df['location_id'].map(lambda x: str(int(x))))
    finished = set(f.split('.')[0] for f in os.listdir('data/posts'))
    return location_ids-finished


def extract_post(posts, post_info, duplicate):
    for post in posts:
        media = post['media']
        taken_at = media['taken_at']
        try:
            like_count = media['like_count']
        except:
            like_count = 0
        try:
            text = media['caption']['text']
        except:
            text = ''
        user = media['user']
        username = user['username']

        ### update bloggers' information
        if username not in duplicate:
            post_info.append((username, taken_at, like_count, text))
            duplicate.add(username)

            bloggers_lock.acquire() # enhance thread safety
            if username not in bloggers:
                bloggers[username] = 1
                bloggers_info.append(list([username, user['full_name'], user['profile_pic_url']]))
            else:
                bloggers[username] += 1
            bloggers_lock.release() # enhance thread safety


def get_posts(location_id):
    time.sleep(random.uniform(0, 3))
    post_info = []
    duplicate = set()

    url = f'https://www.instagram.com/api/v1/locations/{location_id}/sections/'
    payload = {
        'surface': 'grid',
        'tab': 'ranked',
        'max_id': '',
        'next_media_ids': []
    }

    for i in range(2):
        payload['page'] = i
        response = requests.post(url=url, headers=headers, data=payload, cookies=cookies).json()
        if response['status'] == 'fail':
            logging.error("Exceed rate limit. Please renew your IP address.")
            return 


        if not i:
            layout_content = response['sections'][0]['layout_content']
            if 'fill_items' in layout_content:
                posts = layout_content['fill_items']
                extract_post(posts, post_info, duplicate)
            else:
                logging.debug(f'{location_id} has no fill_items.')

        rows = response['sections'][1-i:]
        for row in rows:
            posts = row['layout_content']['medias']
            extract_post(posts, post_info, duplicate)

        payload['max_id'] = response['next_max_id']

    post_df = pd.DataFrame(post_info, columns=["username", "taken_at", "like_count", "text"]).set_index('username', drop=True)
    post_df.to_csv(f'data/posts/{location_id}.csv')


def get_fans(username):
    time.sleep(random.uniform(1, 4))
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    response = requests.get(url=url, headers=headers, cookies=cookies).json()
    bloggers_lock.acquire() # enhance thread safety
    bloggers[username] = response['data']['user']['edge_followed_by']['count']
    bloggers_lock.release() # enhance thread safety


if __name__ == "__main__":
    # global variables
    if os.path.isfile('data/bloggers.csv'):
        bloggers_info = pd.read_csv('data/bloggers.csv').drop('frequency', axis=1).values.tolist()
        bloggers = pd.read_csv('data/bloggers.csv', index_col='Unnamed: 0')['frequency'].to_dict()
    else:
        bloggers_info = []
        bloggers = {}
    bloggers_lock = Lock()
    
    # read locations
    path = 'data/地標.xlsx'
    location_ids = read_location_ids(path)

    # (multi-thread) get posts for locations
    my_queue = Queue()
    for location_id in location_ids:
        my_queue.put(location_id)
    runThreading(my_queue, get_posts, 4)
    logging.info("Get posts success!")

    # create blogger df
    bloggers_df = pd.DataFrame(bloggers_info, columns=["username", "full_name", "profile_pic_url"]).set_index('username', drop=True)
    frequency = pd.DataFrame.from_dict(bloggers, orient='index', columns=['frequency'])
    bloggers_df = pd.merge(bloggers_df, frequency, left_index=True, right_index=True, how='outer')
    bloggers_df.to_csv('data/bloggers.csv')
    logging.info("Finish half!")

    # # (multi-thread) get fans for bloggers
    # headers.pop('content-type')
    # for blogger in bloggers.keys():
    #     my_queue.put(blogger)
    # runThreading(my_queue, get_fans, 4)
    # logging.info("Get fans success!")

    # # update blogger df
    # fans = pd.DataFrame.from_dict(bloggers, orient='index', columns=['fans'])
    # bloggers_df = pd.merge(bloggers_df, fans, left_index=True, right_index=True, how='outer')
    # bloggers_df.to_csv('data/bloggers_with_fans.csv')
    # logging.info("Finish all!")
    

