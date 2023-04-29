import requests
from dotenv import load_dotenv
import os
import pandas as pd
from queue import Queue
from utils.runThreading import runThreading

load_dotenv()
SESSION = os.environ['SESSION']
CRSF = os.environ['CRSF']
cookies = {
    'csrftoken': CRSF,
    'sessionid': SESSION
}

headers = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-full-version-list': '"Chromium";v="112.0.5615.138", "Google Chrome";v="112.0.5615.138", "Not:A-Brand";v="99.0.0.0"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-csrftoken': CRSF,
    'x-ig-app-id': '936619743392459',
    'x-requested-with': 'XMLHttpRequest'
}

post_headers = {
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-full-version-list': '"Chromium";v="112.0.5615.138", "Google Chrome";v="112.0.5615.138", "Not:A-Brand";v="99.0.0.0"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-csrftoken': CRSF,
    'x-ig-app-id': '936619743392459',
    'x-requested-with': 'XMLHttpRequest'
}

def get_fans(full_name):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={full_name}"
    response = requests.get(url=url, headers=headers, cookies=cookies).json()
    return response['data']['user']['edge_followed_by']['count']

def get_posts(location_id):
    post_info = []
    check_duplicate = set()

    url = f'https://www.instagram.com/api/v1/locations/{location_id}/sections/'
    payload = {
        'surface': 'grid',
        'tab': 'ranked',
        'max_id': '',
        'next_media_ids': []
    }

    for i in range(2):
        payload['page'] = i
        response = requests.post(url=url, headers=post_headers, data=payload, cookies=cookies).json()

        rows = response['sections'][1-i:]
        for row in rows:
            cols = row['layout_content']['medias']
            for col in cols:
                media = col['media']
                taken_at = media['taken_at']
                like_count = media['like_count']
                text = media['caption']['text']
                user = media['user']
                username = user['username']

                if username not in check_duplicate:
                    check_duplicate.add(username)
                    post_info.append((username, taken_at, like_count, text))

                    if username not in bloggers:
                        bloggers[username] = 1
                        fans = get_fans(username)
                        bloggers_info.append((username, user['full_name'], user['profile_pic_url'], fans))
                    else:
                        bloggers[username] += 1

        payload['max_id'] = response['next_max_id']

    post_df = pd.DataFrame(post_info, columns=["username", "taken_at", "like_count", "text"]).set_index('username', drop=True)
    post_df.to_csv(f'results/posts/{location_id}.csv')


if __name__ == "__main__":
    # global variables
    bloggers_info = []
    bloggers = {}

    my_queue = Queue()
    location_ids =  ["102098488369787", "109359307435269"]
    for location_id in location_ids:
        my_queue.put(location_id)

    runThreading(my_queue, get_posts, 1)

    bloggers_df = pd.DataFrame(bloggers_info, columns=["username", "full_name", "profile_pic_url", "fans"]).set_index('username', drop=True)
    frequency = pd.DataFrame.from_dict(bloggers, orient='index', columns=['frequency'])
    bloggers_df = pd.merge(bloggers_df, frequency, left_index=True, right_index=True, how='outer')
    bloggers_df.to_csv('results/bloggers.csv')

    print('Test Success!')

