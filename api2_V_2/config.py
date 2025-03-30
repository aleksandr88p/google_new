"""
Конфигурационный файл для модуля GoogleRequester.
Содержит все настройки для запросов к Google.
"""

import logging
from dotenv import load_dotenv
import os
load_dotenv()

# Настройки прокси
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
PROXY_PORT_MIN = int(os.getenv("PROXY_PORT_MIN", "10000"))
PROXY_PORT_MAX = int(os.getenv("PROXY_PORT_MAX", "10999"))
PROXY_PORT_RANGE = (PROXY_PORT_MIN, PROXY_PORT_MAX)
USE_PROXY = True

# Настройки Chrome
CHROME_VERSION = int(os.getenv("CHROME_VERSION", "134"))
HEADLESS = True
TIMEOUT_PAGE_LOAD = int(os.getenv("TIMEOUT_PAGE_LOAD", "30"))


# Настройки для сохранения результатов
RESULTS_FOLDER = "results"
SCREENSHOTS_FOLDER = "screenshots"
SAVE_HTML = False  # Сохранять ли HTML-страницы
SAVE_SCREENSHOTS = False  # Сохранять ли скриншоты
SAVE_FAILED_RESULTS = True  # Сохранять ли результаты при ошибках

# Список User-Agent для ротации
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

# Тексты для кнопок принятия cookies
COOKIE_TEXTS = ['Принять все', 'Accept all', 'I agree', 'Agree', 'Got it']

# Настройки для паузы и отладки
DEFAULT_TEST_PAUSE = 20  # Значение паузы по умолчанию
DEBUG_MODE = False  # Флаг для включения отладочной информации
RANDOM_SLEEP_RANGE_SMALL = (1, 2)  # Пауза между небольшими действиями
RANDOM_SLEEP_RANGE_MEDIUM = (2, 4)  # Пауза для ожидания загрузки страницы

# Настройки поисковых запросов по умолчанию
DEFAULT_SEARCH_DOMAIN = "google.com"
DEFAULT_RESULTS_COUNT = 10
DEFAULT_LANG_INTERFACE = "en"
DEFAULT_LANG_LOCATION = "us"

# Настройки логирования
LOG_LEVEL = logging.INFO
LOG_FILE = "google_requester.log"



# print(PROXY_HOST)
# print(PROXY_USER)
# print(PROXY_PASS)
# print(PROXY_PORT_MIN)
# print(PROXY_PORT_MAX)
# print(USE_PROXY)


# print(f"HEADLESS value: {HEADLESS}, type: {type(HEADLESS)}")