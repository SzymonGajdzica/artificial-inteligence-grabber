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
        with open('results/used_app_ids.txt', mode='r') as file:
            self.used_app_ids.update(map(lambda line: line.strip(), file.readlines()))
        with open('results/bad_app_ids.txt', mode='r') as file:
            self.bad_app_ids.update(map(lambda line: line.strip(), file.readlines()))

    def read_source_files(self):
        with open('input/app_ids.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.app_ids.add(row['packageName'].strip())


class SessionHandler:
    session = None

    def __init__(self):
        self.restart_session()

    def restart_session(self):
        self.session = requests.session()
        self.session.proxies = {'http': 'socks5://127.0.0.1:9150',
                                'https': 'socks5://127.0.0.1:9150'}

    def get_string(self, link):
        try:
            return str(self.session.get(link).text)
        except ConnectionError:
            self.restart_session()
            return self.get_string(link)


def parse_line(line):
    sliced = line.replace(r'\\"', r"\'").replace(r'\"', r"\'").split(sep=r'"')
    return sliced[2].replace(',', '').replace('null', '')[-1], sliced[3]


def fetch_from_link(session_handler, link):
    return list(map(lambda n_line: parse_line(n_line),
                    filter(lambda m_line: 'photo.jpg"]\n]\n]' in m_line,
                           session_handler.get_string(link).split(sep=r'null,null'))))


if __name__ == '__main__':
    data_holder = DataHolder()
    session_handler = SessionHandler()
    with tqdm.trange(len(data_holder.app_ids)) as bar:
        for app_id in data_holder.app_ids:
            bar.update(1)
            if app_id not in data_holder.used_app_ids and app_id not in data_holder.bad_app_ids:
                if random.random() <= 0.001:
                    session_handler.restart_session()
                results = fetch_from_link(session_handler,
                                          '{0}{1}{2}'.format(link_prefix, app_id, link_suffix))
                if len(results) != 0:
                    with open('results/result.tsv', mode='a', encoding="utf-8") as result_file:
                        for rating, comment in results:
                            result_file.write('{0}\t"{1}"\n'.format(rating, comment))
                    data_holder.used_app_ids.add(app_id)
                    with open('results/used_app_ids.txt', mode='a', encoding="utf-8") as used_app_ids_file:
                        used_app_ids_file.write('{0}\n'.format(app_id))
                else:
                    data_holder.bad_app_ids.add(app_id)
                    with open('results/bad_app_ids.txt', mode='a', encoding="utf-8") as bad_app_ids_file:
                        bad_app_ids_file.write('{0}\n'.format(app_id))
