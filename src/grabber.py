import csv
import random

import requests
import tqdm

link_prefix = 'https://play.google.com/store/apps/details?id='
link_suffix = '&showAllReviews=true&hl=en'


class DataHolder:
    used_app_ids = set()
    bad_app_ids = set()
    app_ids = set()

    def __init__(self):
        self.read_source_files()
        self.read_helper_files()

    def read_helper_files(self):
        with open('used_app_ids.txt', mode='r') as file:
            self.used_app_ids.update(map(lambda line: line[:-1], file.readlines()))
        with open('bad_app_ids.txt', mode='r') as file:
            self.bad_app_ids.update(map(lambda line: line[:-1], file.readlines()))

    def read_source_files(self):
        with open('app_ids.csv', mode='r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                self.app_ids.add(row['packageName'])


class SessionHandler:
    session = None

    def __init__(self):
        self.restart_session()

    def restart_session(self):
        self.session = requests.session()
        self.session.proxies = {'http': 'socks5://127.0.0.1:9150',
                                'https': 'socks5://127.0.0.1:9150'}


def parse_line(line):
    sliced = line.split(sep=r'"')
    return sliced[2].replace(',', '').replace('null', '')[-1].replace(r'\\"', r"'").replace(r'"', r"'").replace(r"\'",
                                                                                                                r"'"), \
           sliced[3]


def fetch_from_link(session, link):
    return list(map(lambda n_line: parse_line(n_line),
                    filter(lambda m_line: 'photo.jpg"]\n]\n]' in m_line,
                           str(session.get(link).text)
                           .split(sep=r'null,null'))))


if __name__ == '__main__':
    data_holder = DataHolder()
    session_handler = SessionHandler()
    with open('result.csv', mode='a', encoding="utf-8") as result_file:
        with tqdm.tqdm(total=len(data_holder.app_ids), desc="Adding comments with rating",
                       bar_format="{l_bar}{bar} [ time left: {remaining} ]") as bar:
            for app_id in data_holder.app_ids:
                bar.update(1)
                if random.random() <= 0.001:
                    session_handler.restart_session()
                if app_id not in data_holder.used_app_ids and app_id not in data_holder.bad_app_ids:
                    results = fetch_from_link(session_handler.session,
                                              '{0}{1}{2}'.format(link_prefix, app_id, link_suffix))
                    for rating, comment in results:
                        result_file.write('{0}\t"{1}"\n'.format(rating, comment))
                    if len(results) != 0:
                        data_holder.used_app_ids.add(app_id)
                        with open('used_app_ids.txt', mode='a', encoding="utf-8") as file:
                            file.write('{0}\n'.format(app_id))
                    else:
                        data_holder.bad_app_ids.add(app_id)
                        with open('bad_app_ids.txt', mode='a', encoding="utf-8") as file:
                            file.write('{0}\n'.format(app_id))
