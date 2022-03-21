import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
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


def get_config() -> dict:
    if os.path.exists('cfg.yaml'):
        with open('cfg.yaml') as f:
            config = yaml.safe_load(f)
            return config


def set_config(dictionary: dict) -> None:
    with open('cfg.yaml', 'w') as f:
        yaml.dump(dictionary, f)


def delete_file(file_name: str) -> None:
    """Удаление файла(для отладки)"""
    os.remove(file_name)


def dump_binary(data: dict, file_name: str) -> None:
    """Загрузка в бинарный файл"""
    with open(file_name, 'wb') as bin_file_write:
        pickle.dump(data, bin_file_write)


def load_binary(file_name: str) -> dict:
    """Загрузка из бинарного файла"""
    with open(file_name, 'rb') as bin_file_read:
        return pickle.load(bin_file_read)


def download_page(url: str) -> str:
    """Скачивание html кода сайтов"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response = session.get(url, headers=headers)
    assert response.status_code != 404, 'Неправильный url запрос'
    assert response.status_code != 400, 'Немного неправильный url запрос'
    assert response.status_code == 200, 'Нет соединения с сервером: Ошибка ' + str(response.status_code)

    return response.text


def download_all_htmls(is_iad: bool, articles_per_page: int, num_of_pages: int) -> dict:
    """Скачивание рандомных страниц """
    search_address = 'https://arxiv.org/search/cs?searchtype=all&query='
    search_option = '&abstracts=show&order=-submitted_date&size=' + \
                    str(articles_per_page) + '&date-date_type=submitted_date'
    query_options = IAD_OPTIONS if is_iad else NOT_IAD_OPTIONS
    all_htmls = dict()
    for search_key_words in query_options:
        html = download_page(search_address + search_key_words + search_option + '&start=0')
        soup = BeautifulSoup(html, 'lxml')
        total_num_of_articles_html = soup.find('h1', {'class': 'title'})
        assert len(total_num_of_articles_html) > 0, "Общее количество статей не распознано"
        total_num_of_articles = int(total_num_of_articles_html.text.split()[3].replace(',', '').replace(';', ''))
        if total_num_of_articles > 10000:
            total_num_of_articles = 10000

        pages_list = list(range(int(total_num_of_articles / articles_per_page - 1)))
        random_pages = random.sample(pages_list, num_of_pages + 2)  # Рандомные страницы
        query_htmls = list()
        for page in random_pages:
            search_start = '&start=' + str(page * articles_per_page)
            query_htmls.append(download_page(search_address + search_key_words + search_option + search_start))
        all_htmls[search_key_words] = query_htmls
    return all_htmls


def parse(is_iad: bool, all_htmls: dict, articles_per_query: int) -> dict:
    """Парсинг загруженных из файла страниц"""
    all_articles_structured = dict()
    iad_dict_articles = dict()
    all_articles = list()
    if not is_iad:
        if os.path.exists('IAD.bin'):
            iad_dict_articles = load_binary('IAD.bin')
        else:
            return {}
    iad_articles = [article for query in iad_dict_articles.values() for article in query]

    for key, query_htmls in all_htmls.items():
        articles = list()
        for html in query_htmls:
            soup = BeautifulSoup(html, 'lxml')
            for article in soup.find_all('li', {'class': 'arxiv-result'}):

                article_url = article.find('p', {'class': 'list-title'}).a['href']
                assert len(article_url) > 0, "url не распознано"

                title_html = article.find('p', {'class': 'title'})
                assert len(title_html) > 0, "Название статьи не распознано"
                title = title_html.text.strip()

                tags_html = article.find('div', {'class': 'tags'}).find_all('span', {'class': 'tag'})
                assert len(tags_html) > 0, "Теги не распознаны"
                tag_codes = list()
                tag_names = list()
                for tag in tags_html:
                    tag_names.append(tag['data-tooltip'])
                    tag_codes.append(tag.text)

                authors_html = article.find('p', {'class': 'authors'}).find_all('a')
                assert len(authors_html) > 0, "Имена авторов не распознаны"
                authors = list()
                for author in authors_html:
                    authors.append(author.text)

                # Текст без кнопки Less
                abstract_html = article.find('span', {'class': 'abstract-full'})
                assert len(abstract_html) > 0, "Описание текста статьи не распознано"
                abstract = abstract_html.text.strip().split('\n')[0]

                submission_date_html = article.find('p', {'class': 'is-size-7'})
                assert len(submission_date_html) > 0, "Дата публикации не распознана"
                submission_date = submission_date_html.contents[1].strip()[:-1]

                article = {
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
                if article not in all_articles:
                    if article not in iad_articles:
                        articles.append(article)
                        all_articles.append(article)

        all_articles_structured[key] = random.sample(articles, articles_per_query)

    return all_articles_structured
