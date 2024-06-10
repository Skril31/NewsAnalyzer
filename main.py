import requests
from bs4 import BeautifulSoup
import sqlite3
import annotation
import time
import entity
import urllib3
import ssl
import urllib.request, urllib.parse, urllib.error
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

urllib3.disable_warnings()

headers = requests.utils.default_headers()

headers.update(
    {
        'User-Agent': 'My User Agent 1.0',
    }
)

# Создаем подключение к базе данных SQLite
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

# Создаем таблицу для новостей, если она еще не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT,
        content TEXT,
        annotation TEXT,
        name_entity TEXT,
        flag_annotation TEXT,
        flag_news TEXT
    )
''')

def parse_sledcom_page(url):
    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим последнюю загруженную новость
        latest_news_block = soup.find('div', class_='bl-item clearfix')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            titles = latest_news_block.find_all('a')
            title = titles[1].text.strip()
            news_url = 'https://volgograd.sledcom.ru' + titles[1]['href']
            content = parse_sledcom_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%volgograd.sledcom.ru%"))
                # Вставуф ляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (title, news_url, content, '-', '-', '0', '0'))
                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)
                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_sledcom_content(url):
    response = requests.get(url,verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент <article>, содержащий текст новости
    article = soup.find('article')

    # Ищем все параграфы
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
    return content

def parse_mvd_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим последнюю загруженную новость
        latest_news_block = soup.find('div', class_='sl-item-title')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a').text.strip()
            news_url = 'https://34.xn--b1aew.xn--p1ai/' + latest_news_block.find('a')['href']
            content = parse_mvd_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%34.xn--b1aew.xn--p1ai%"))

                # Вставуф ляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (title, news_url, content, '-', '-', '0', '0'))
                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)
            else:
                print("Новых новостей нет!")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_mvd_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент <article>, содержащий текст новости
    article = soup.find('div', class_='article')

    # Ищем все параграфы
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
    return content

def parse_volgadmin_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим последнюю загруженную новость
        latest_news_block = soup.find('div', class_='news_item')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            titles = latest_news_block.find_all('a')
            title = titles[1].text.strip()
            news_url = 'https://www.volgadmin.ru/d' + titles[1]['href']
            content = parse_volgadmin_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%volgadmin.ru%"))
                # Вставуф ляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (title, news_url, content, '-', '-', '0', '0'))
                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)
            else:
                print("Новых новостей нет!")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_volgadmin_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент <article>, содержащий текст новости
    article = soup.find('div', class_='rightcol')

    # Ищем все параграфы
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
    return content

def parse_volgograd_news_page(url):
    try:
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим последнюю загруженную новость
        latest_news_block = soup.find('div', class_='col-md-12 news-item')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a').text.strip()
            news_url = 'https://www.volgograd.ru' + latest_news_block.find('a')['href']
            content = parse_volgograd_news_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%volgograd.ru%"))
                # Вставуф ляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (title, news_url, content, '-', '-', '0', '0'))
                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")


def parse_volgograd_news_content(url):
    try:
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент <article>, содержащий текст новости
        article = soup.find('div', class_='news-detail')

    # Ищем все параграфы
        paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
        content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
        return content
    
    except:
        print("Ошибка при получении данных из")
# Функция для парсинга страницы с новостями на сайте TASS
def parse_news_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим последнюю загруженную новость
        latest_news_block = soup.find('a', class_='tass_pkg_link-v5WdK')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            #title = latest_news_block.find( 'span', class_='ds_ext_title-1XuEF').text.strip()
            title = latest_news_block.find( 'span', class_='tass_pkg_title-xVUT1').text.strip()
            news_url = 'https://tass.ru' + latest_news_block['href']
            content = parse_news_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%tass.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))
                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")


# Функция для парсинга текста новости на сайте TASS
def parse_news_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        article = soup.find('article')
    
        paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
        content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

        
    except: 
         response = requests.get(url)
         soup = BeautifulSoup(response.text, 'html.parser')
         article = soup.find( class_='news')
         paragraphs = article.find_all('p')
         content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
         return content
    finally:
         return content

# Функция для парсинга страницы с новостями на сайте Генпрокуратуры
def parse_genproc_page(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим последнюю добавленную новость
        latest_news_block = soup.find('div', class_='feeds-main-page-portlet__list_item')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a', class_='feeds-main-page-portlet__list_text').text.strip()
            news_url = latest_news_block.find('a', class_='feeds-main-page-portlet__list_text')['href']
            content = parse_genproc_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%genproc.gov.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))
                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

# Функция для парсинга текста новости на сайте Генпрокуратуры
def parse_genproc_content(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент с классом feeds-page__article_text
    article_text = soup.find('div', class_='feeds-page__article_text')

    # Ищем все параграфы внутри элемента
    paragraphs = article_text.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

    return content


def parse_vesti_page(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='list__item')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('h3', class_='list__title').text.strip()
            news_url = 'https://www.vesti.ru' + latest_news_block.find('a', href=True)['href']
            content = parse_vesti_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%vesti.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")


def parse_vesti_content(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент с классом js-mediator-article
    article = soup.find('div', class_='js-mediator-article')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

    return content

def parse_rpn_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='newsPreview__description')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a', class_='text _dark _news').text.strip()
            news_url = 'https://rpn.gov.ru' + latest_news_block.find('a', href=True)['href']
            content = parse_rpn_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%rpn.gov.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_rpn_content(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент с классом js-mediator-article
    article = soup.find('div', class_='ui')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

    return content

def parse_ria_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='list-item__content')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a', class_='list-item__title color-font-hover-only').text.strip()
            news_url = latest_news_block.find('a', href=True)['href']
            content = parse_ria_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%ria.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_ria_content(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент с классом js-mediator-article
    article = soup.find('div', class_='article__body js-mediator-article mia-analytics')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('div', class_='article__text')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

    return content

def parse_rospotrebnadzor_page(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='news-name')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a', ).text.strip()
            news_url = url + latest_news_block.find('a', href=True)['href']
            content = parse_rospotrebnadzor_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%34.rospotrebnadzor.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_rospotrebnadzor_content(url):
    response = requests.get(url, headers=headers, )
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент с классом js-mediator-article
    article = soup.find('div', class_='bx_item_description')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
    if content == "":
        content = article.text

    return content

def parse_oblzdrav_page(url):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        #response = requests.get(url, headers=headers)
        html = urllib.request.urlopen(url, context=ctx).read()
        soup = BeautifulSoup(html, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='col-md-12 news-item')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a', ).text.strip()
            news_url = url + latest_news_block.find('a', href=True)['href']
            content = parse_oblzdrav_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%oblzdrav.volgograd.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_oblzdrav_content(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    html = urllib.request.urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')
    introduction = soup.find('div', class_='col-md-12 col-sm-12 col-xs-12')
    introductionArts = introduction.find_all('p')
    # Находим элемент с классом js-mediator-article
    article = soup.find('div', id='full_text')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
    content = introductionArts.pop().text + content

    return content

def parse_zmsut_page(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='bl-item-title')

        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a').text.strip()
            news_url = 'https://zmsut.sledcom.ru' + latest_news_block.find('a', href=True)['href']
            content = parse_zmsut_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%zmsut.sledcom.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_zmsut_content(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим элемент с классом js-mediator-article
    article = soup.find('article', class_='c-detail m_b4')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

    return content

def parse_fssp_page(url):
    # Настройка Selenium с использованием ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Опционально: запуск браузера в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Укажите путь к ChromeDriver
    chrome_driver_path = "D:/pyProjects/news/chromedriver.exe"

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        # Явное ожидание элемента, чтобы быть уверенным, что контент загружен
        wait = WebDriverWait(driver, 10)
        latest_news_block = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-17qmyy2-CardDesc")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Находим блок с классом list__item
        latest_news_block = soup.find('div', class_='css-17qmyy2-CardDesc')
        driver.quit()
        # Проверяем, что новость найдена
        if latest_news_block:
            # Находим заголовок, ссылку и текст новости
            title = latest_news_block.find('a').text.strip()
            news_url = 'https://r34.fssp.gov.ru' + latest_news_block.find('a', href=True)['href']
            content = parse_fssp_content(news_url)

            # Проверяем, не добавлена ли уже эта новость в базу данных
            cursor.execute('SELECT id FROM news WHERE url=?', (news_url,))
            existing_news = cursor.fetchone()
            if not existing_news:
                cursor.execute("DELETE FROM news WHERE flag_news = ? and url like ?", (1, "%zmsut.sledcom.ru%"))
                # Вставляем данные в базу данных
                cursor.execute('INSERT INTO news (title, url, content, annotation, name_entity, flag_annotation, flag_news) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (title, news_url, content, '-', '-', '0', '0'))

                conn.commit()
                print(f"Обнаружена новая новость: {news_url}")

                # Добавление сущностей
                cursor.execute("SELECT content FROM news")
                texts = cursor.fetchall()
                entity.names_entity(texts)

                cursor.execute("SELECT content FROM news WHERE flag_annotation = 0")
                texts = cursor.fetchall()
                annotation.create_neural_annotations(texts)

            else:
                print("Новых новостей нет!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных из {url}: {e}")

def parse_fssp_content(url):
    # Настройка Selenium с использованием ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Опционально: запуск браузера в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Укажите путь к ChromeDriver
    chrome_driver_path = "D:/pyProjects/news/chromedriver.exe"

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    latest_news_block = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-1gqte2e-NewsOneType2Content")))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    # Находим элемент с классом js-mediator-article
    article = soup.find('div', class_='css-1gqte2e-NewsOneType2Content')

    # Ищем все параграфы внутри элемента
    paragraphs = article.find_all('p')

    # Собираем текст новости из всех параграфов
    content = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

    return content
# Основной код
if __name__ == '__main__':
    i = 0
    while True:
        i += 1
        print(f"{i}-й прогон")
        parse_sledcom_page('https://volgograd.sledcom.ru/')
        parse_mvd_page('https://34.xn--b1aew.xn--p1ai/%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8')
        parse_volgadmin_page('https://www.volgadmin.ru/d/list/news/admvlg')
        parse_genproc_page('https://epp.genproc.gov.ru/web/proc_34')
        parse_vesti_page('https://www.vesti.ru/search?q=%D0%B2%D0%BE%D0%BB%D0%B3%D0%BE%D0%B3%D1%80%D0%B0%D0%B4&type=news&sort=date')
        parse_news_page('https://tass.ru/tag/volgogradskaya-oblast')
        parse_volgograd_news_page('https://www.volgograd.ru/news/')
        parse_rpn_page('https://rpn.gov.ru/regions/34/news')
        parse_ria_page('https://ria.ru/search/?query=волгоград')
        parse_rospotrebnadzor_page('https://34.rospotrebnadzor.ru')
        parse_oblzdrav_page('https://oblzdrav.volgograd.ru')
        parse_zmsut_page('https://zmsut.sledcom.ru/search?q=волгоград&radio_group=on&sort=date&from=&to=')
        parse_fssp_page('https://r34.fssp.gov.ru/press-sluzhba/news')
        
		
		
        time.sleep(60)

# Закрываем подключение к базе данных
conn.close()


