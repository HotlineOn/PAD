import os
import requests
import pickle
import yaml
from bs4 import BeautifulSoup
import random

IAD_OPTIONS = [
    'data+mining',
]
NOT_IAD_OPTIONS = [
    'hardware+architecture',
    'software+engineering',
    'fuzzy+logic',
    'modeling',
    'databases',
    'computer+security',
]


def get_random_articles(articles: list, num_of_articles: int) -> list:
    return random.sample(articles, num_of_articles)


def get_config() -> dict:
    if os.path.exists('cfg.yaml'):
        with open('cfg.yaml') as f:
            config = yaml.safe_load(f)
            return config


def set_config(dictionary: dict) -> None:
    with open('cfg.yaml', 'w') as f:
        yaml.dump(dictionary, f)


def make_urls(is_iad: bool, articles_per_page: int, num_of_pages: int) -> list:
    """Синтез url адресов"""
    search_address = 'https://arxiv.org/search/cs?query='
    search_option = '&searchtype=all&abstracts=show&order=-announced_date_first&size=' + \
                    str(articles_per_page) + '&date-date_type=submitted_date'
    query = IAD_OPTIONS if is_iad else NOT_IAD_OPTIONS
    urls = list()
    for option in query:
        for page in range(num_of_pages):
            search_start = '&start=' + str(page * articles_per_page)
            urls.append(search_address + option + search_option + search_start)
    return urls


def delete_file(file_name: str) -> None:
    """Удаление файла(для отладки)"""
    os.remove(file_name)


def dump_binary(file_name: str, data: list) -> None:
    """Загрузка в бинарный файл"""
    with open(file_name, 'wb') as bin_file_write:
        pickle.dump(data, bin_file_write)


def load_binary(file_name: str) -> list:
    """Загрузка из бинарного файла"""
    with open(file_name, 'rb') as bin_file_read:
        return pickle.load(bin_file_read)


def download(urls: list, file_name: str) -> None:
    """Скачивание с сайта в файл"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}
    htmls = list()
    for url in urls:
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, 'Нет соединения с сервером'
        htmls.append(response.text)
    dump_binary(file_name, htmls)


def parse(file_name: str) -> list:
    """Парсинг загруженных из файла страниц"""
    articles = []
    htmls = load_binary(file_name)
    for html in htmls:
        soup = BeautifulSoup(html, 'lxml')
        for article in soup.find_all('li', {'class': 'arxiv-result'}):
            article_url = article.find('p', {'class': 'list-title'}).a['href']
            assert len(article_url) > 0, "url не распознано"
            title_html = article.find('p', {'class': 'title'})
            assert len(title_html) > 0, "Название статьи не распознано"
            title = title_html.text.strip()
            tags_html = article.find('div', {'class': 'tags'}).find_all('span', {'class': 'tag'})
            assert len(tags_html) > 0, "Теги не распознаны"
            tag_codes = []
            tag_names = []
            for tag in tags_html:
                try:
                    tag_names.append(tag['data-tooltip'])
                    tag_codes.append(tag.text)
                except KeyError:
                    pass
            assert len(tag_codes) == len(tag_names), 'Длины списка кодов и списка имён тегов не совпадает' + \
                                                     str(len(tag_codes)) + ' ' + str(len(tag_names))
            authors_html = article.find('p', {'class': 'authors'}).find_all('a')
            assert len(authors_html) > 0, "Имена авторов не распознаны"
            authors = []
            for author in authors_html:
                authors.append(author.text)
            # Текст без кнопки Less
            abstract_html = article.find('span', {'class': 'abstract-full'}).text
            assert len(abstract_html) > 0, "Описание текста статьи не распознано"
            abstract = abstract_html.strip().split('\n')[0]
            submission_date_html = article.find('p', {'class': 'is-size-7'})
            assert len(submission_date_html) > 0, "Дата публикации не распознана"
            submission_date = submission_date_html.contents[1].strip()[:-1]
            articles.append(
                {
                    'url': article_url,
                    'title': title,
                    'tags':
                        {
                            'codes': tag_codes,
                            'names': tag_names
                        },
                    'authors': authors,
                    'abstract': abstract,
                    'submitted': submission_date
                }
            )
    return articles
