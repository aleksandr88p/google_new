"""
Асинхронный модуль для выполнения запросов к Google и получения HTML-страниц результатов поиска.
Использует undetected_chromedriver для обхода блокировок.
"""

import undetected_chromedriver as uc
import time
import random
import json
import os
import shutil
import urllib.parse
import base64
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from selenium.webdriver.common.keys import Keys

# Импорт конфигурационных настроек
import config

# Настройка логирования
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger('google_requester')


class GoogleRequester:
    """
    Класс для выполнения запросов к Google с использованием undetected_chromedriver.
    Поддерживает работу через прокси и сохранение HTML-страниц результатов.
    """
    
    def __init__(self):
        """Инициализация класса GoogleRequester."""
        self.driver = None
        self.current_proxy = None
        self.current_user_agent = None
        
        # Создаем необходимые директории
        os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
        os.makedirs(config.SCREENSHOTS_FOLDER, exist_ok=True)
    
    def create_uule_parameter(self, location: Optional[str]) -> Optional[str]:
        """
        Создает UULE параметр для имитации местоположения в Google.
        
        Args:
            location: Название города или местоположения, например 'Barcelona,Catalonia,Spain'
        
        Returns:
            Закодированная строка UULE для использования в URL или None, если location не указан
        """
        if not location:
            return None
            
        # Формат UULE: "w+CAIQICI" + base64(location)
        encoded_location = base64.b64encode(location.encode()).decode()
        return f"w+CAIQICI{encoded_location}"
    
    def create_proxy_extension(self, proxy_host: str, proxy_port: str, 
                              proxy_user: str, proxy_pass: str, 
                              ext_dir: str = "proxy_auth_extension") -> str:
        """
        Создает расширение для Chrome для аутентификации прокси.
        
        Args:
            proxy_host: Хост прокси-сервера
            proxy_port: Порт прокси-сервера
            proxy_user: Имя пользователя для прокси
            proxy_pass: Пароль для прокси
            ext_dir: Директория для расширения
            
        Returns:
            Абсолютный путь к директории расширения
        """
        # Удаляем директорию расширения, если она существует
        if os.path.exists(ext_dir):
            shutil.rmtree(ext_dir)
        
        # Создаем директорию для расширения
        os.makedirs(ext_dir)
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "76.0.0"
        }
        """

        background_js = f"""
        var config = {{
                mode: "fixed_servers",
                rules: {{
                    singleProxy: {{
                        scheme: "http",
                        host: "{proxy_host}",
                        port: parseInt({proxy_port})
                    }},
                    bypassList: ["localhost"]
                }}
            }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_user}",
                    password: "{proxy_pass}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """
        
        # Записываем файлы расширения
        with open(os.path.join(ext_dir, "manifest.json"), "w") as f:
            f.write(manifest_json)
        
        with open(os.path.join(ext_dir, "background.js"), "w") as f:
            f.write(background_js)
        
        return os.path.abspath(ext_dir)
    
    def setup_chrome_options(self) -> uc.ChromeOptions:
        """
        Настраивает опции Chrome для автоматизации.
        
        Returns:
            ChromeOptions: Настроенные опции Chrome
        """
        options = uc.ChromeOptions()
        
        # Настройки для скрытия автоматизации
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        
        # Случайное разрешение экрана
        screen_width = random.randint(1200, 1920)
        screen_height = random.randint(800, 1080)
        options.add_argument(f'--window-size={screen_width},{screen_height}')
        
        # Случайный User-Agent
        self.current_user_agent = random.choice(config.USER_AGENTS)
        options.add_argument(f'--user-agent={self.current_user_agent}')
        
        return options
    
    def get_rotating_proxy(self) -> Tuple[str, str, str, str]:
        """
        Возвращает прокси с ротацией портов.
        
        Returns:
            Кортеж (proxy_host, proxy_port, proxy_user, proxy_pass)
        """
        proxy_port = str(random.randint(*config.PROXY_PORT_RANGE))
        self.current_proxy = f"{config.PROXY_HOST}:{proxy_port}"
        logger.info(f"Используем прокси: {self.current_proxy}")
        return config.PROXY_HOST, proxy_port, config.PROXY_USER, config.PROXY_PASS
    
    def initialize_driver(self) -> None:
        """
        Инициализирует и настраивает драйвер Chrome.
        """
        try:
            options = self.setup_chrome_options()
            
            # Подключаем прокси, если они включены
            if config.USE_PROXY:
                # Получаем ротирующийся прокси
                proxy_host, proxy_port, proxy_user, proxy_pass = self.get_rotating_proxy()
                
                # Создаем расширение для прокси
                ext_path = self.create_proxy_extension(proxy_host, proxy_port, proxy_user, proxy_pass)
                logger.info(f"Расширение для прокси создано в: {ext_path}")
                
                # Загружаем расширение для прокси
                options.add_argument(f'--load-extension={ext_path}')
            

            print(f"HEADLESS value: {config.HEADLESS}, type: {type(config.HEADLESS)}")
            # Создаем экземпляр Chrome
            if config.HEADLESS:
                print("HEADLESS  HEADLESS  HEADLESS  HEADLESS  HEADLESS")
                options.headless = True
                options.add_argument('--headless')  # Для Chrome 109+
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=config.CHROME_VERSION,
                headless=config.HEADLESS
            )
            
            # Устанавливаем тайм-аут загрузки страницы
            self.driver.set_page_load_timeout(config.TIMEOUT_PAGE_LOAD)
            
            # Скрываем факт автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Драйвер Chrome успешно инициализирован")
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации драйвера: {str(e)}")
            if self.driver:
                self.close_driver()
            raise
    
    def close_driver(self) -> None:
        """Закрывает драйвер Chrome, если он открыт."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Драйвер Chrome закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии драйвера: {str(e)}")
    
    def accept_cookies(self) -> None:
        """Принимает cookies, если появилось соответствующее окно."""
        try:
            for cookie_text in config.COOKIE_TEXTS:
                buttons = self.driver.find_elements('xpath', f'//button[contains(text(), "{cookie_text}")]')
                if buttons:
                    buttons[0].click()
                    logger.info(f"Приняты куки (нажата кнопка '{cookie_text}')")
                    time.sleep(random.uniform(1, 2))
                    return
        except Exception as e:
            logger.warning(f"Ошибка при принятии куков: {e}")

    def handle_location_dialog(self) -> bool:
        """
        Обрабатывает диалоговое окно запроса геолокации Google.
        Нажимает кнопку "Not now" ("Не сейчас").
        
        Returns:
            bool: True, если диалог был найден и обработан, False в противном случае
        """
        try:
            # Ждем немного, чтобы диалог успел появиться
            time.sleep(1.5)
            
            # Попробуем найти диалоговое окно по классам (не зависит от языка)
            dialog = self.driver.find_elements('css selector', 'div.qk7LXc[role="dialog"]')
            
            if dialog:
                logger.info("Обнаружено диалоговое окно геолокации")
                
                # Вариант 1: Нажать кнопку "Not now" по классу
                not_now_buttons = self.driver.find_elements('css selector', 'div.mpQYc g-raised-button')
                if not_now_buttons:
                    not_now_buttons[0].click()
                    logger.info("Нажата кнопка 'Not now'")
                    time.sleep(1)
                    return True
                
                # Вариант 2: Если первый вариант не сработал, попробуем по XPath
                not_now_xpath = '//g-raised-button[.//div[contains(text(), "Not now") or contains(text(), "Не сейчас")]]'
                not_now_elements = self.driver.find_elements('xpath', not_now_xpath)
                if not_now_elements:
                    not_now_elements[0].click()
                    logger.info("Нажата кнопка 'Not now' (через XPath)")
                    time.sleep(1)
                    return True
                    
                # Вариант 3: Если кнопки не найдены, нажмем на последнюю кнопку в диалоге
                buttons = self.driver.find_elements('css selector', 'g-raised-button')
                if len(buttons) > 0:
                    buttons[-1].click()  # Нажимаем на последнюю кнопку
                    logger.info("Нажата последняя кнопка в диалоге")
                    time.sleep(1)
                    return True
                    
                # Вариант 4: Закрыть диалог через Escape
                self.driver.find_element('tag name', 'body').send_keys(Keys.ESCAPE)
                logger.info("Отправлена клавиша Escape для закрытия диалога")
                time.sleep(1)
                return True
                
            return False
        
        except Exception as e:
            logger.warning(f"Ошибка при обработке диалога геолокации: {e}")
            return False
    
    def build_search_url(self, query: str, domain: str = "google.com", 
                        num: int = 10, gl: Optional[str] = None, 
                        hl: Optional[str] = None, lr: Optional[str] = None, 
                        cr: Optional[str] = None, location: Optional[str] = None) -> str:
        """
        Строит URL для поискового запроса Google.
        
        Args:
            query: Поисковый запрос
            domain: Домен Google (google.com, google.ru и т.д.)
            num: Количество результатов
            gl: Параметр геолокализации
            hl: Язык интерфейса
            lr: Язык результатов
            cr: Страна результатов
            location: Строка с местоположением
            
        Returns:
            URL для поискового запроса
        """
        # Базовые параметры запроса
        search_params = {
            'q': query,           # поисковый запрос
            'hl': hl or 'en',     # язык интерфейса
            'gl': gl or 'us',     # локализация поиска
            'num': num,           # количество результатов
            'ie': 'UTF-8',        # кодировка входных данных
            'oe': 'UTF-8',        # кодировка выходных данных
            'pws': 0,             # отключить персонализацию поиска
        }
        search_params['complete'] = '0'  # Отключает некоторые фильтры Google

        
        # Добавляем необязательные параметры
        if lr:
            search_params['lr'] = lr
        if cr:
            search_params['cr'] = cr
            
        # Добавляем параметры локации только если она указана
        if location:
            uule_param = self.create_uule_parameter(location)
            near_param = location.split(',')[0]
            
            search_params['uule'] = uule_param
            search_params['near'] = near_param
            logger.info(f"Задано местоположение: {location}")
        
        # Формируем URL
        base_url = f"https://www.{domain}"
        query_string = urllib.parse.urlencode(search_params)
        search_url = f"{base_url}/search?{query_string}"
        
        return search_url
    
    def check_for_captcha(self, page_source: str) -> bool:
        """
        Проверяет наличие капчи на странице.
        
        Args:
            page_source: HTML-код страницы
            
        Returns:
            True, если обнаружена капча, иначе False
        """
        page_source_lower = page_source.lower()
        captcha_markers = ['recaptcha', 'я не робот', 'i\'m not a robot']
        return any(marker in page_source_lower for marker in captcha_markers)
    
    def save_results(self, query: str, page_source: str, success: bool = True, 
                    error: str = "", test_pause: int = 0) -> Dict[str, str]:
        """
        Сохраняет результаты запроса (HTML и скриншот).
        
        Args:
            query: Поисковый запрос
            page_source: HTML-код страницы
            success: Флаг успешности запроса
            error: Текст ошибки (если есть)
            test_pause: Пауза для тестирования
            
        Returns:
            Словарь с путями к сохраненным файлам
        """
        result = {}
        
        # Генерируем имена файлов на основе запроса и времени
        timestamp = int(time.time())
        sanitized_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
        html_filename = f"{sanitized_query}_{timestamp}.html"
        screenshot_filename = f"{sanitized_query}_{timestamp}.png"
        
        html_path = os.path.join(config.RESULTS_FOLDER, html_filename)
        screenshot_path = os.path.join(config.SCREENSHOTS_FOLDER, screenshot_filename)
        
        # Сохраняем HTML только если установлен соответствующий флаг
        if config.SAVE_HTML and (success or config.SAVE_FAILED_RESULTS):
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info(f"HTML сохранен в {html_path}")
            result["html_path"] = html_path
        
        # Сохраняем скриншот только если установлен соответствующий флаг
        if config.SAVE_SCREENSHOTS and (success or config.SAVE_FAILED_RESULTS) and self.driver:
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Скриншот сохранен в {screenshot_path}")
            result["screenshot_path"] = screenshot_path
        
        # Если задана пауза для тестирования - ждем
        if test_pause > 0:
            logger.info(f"Пауза для тестирования: {test_pause} сек.")
            time.sleep(test_pause)
        
        return result
    
    async def search_google_async(self, query: str, domain: str = None, 
                                num: int = None, gl: Optional[str] = None, 
                                hl: Optional[str] = None, lr: Optional[str] = None, 
                                cr: Optional[str] = None, location: Optional[str] = None,
                                test_pause: int = None) -> Dict[str, Any]:
        """
        Асинхронно выполняет поисковый запрос к Google.
        
        Args:
            query: Поисковый запрос
            domain: Домен Google
            num: Количество результатов
            gl: Параметр геолокализации
            hl: Язык интерфейса
            lr: Язык результатов
            cr: Страна результатов
            location: Строка с местоположением
            test_pause: Пауза для тестирования в секундах
            
        Returns:
            Словарь с результатами запроса
        """
        # Используем значения из конфигурации, если параметры не указаны явно
        domain = domain or config.DEFAULT_SEARCH_DOMAIN
        num = num or config.DEFAULT_RESULTS_COUNT
        gl = gl or config.DEFAULT_LANG_LOCATION
        hl = hl or config.DEFAULT_LANG_INTERFACE
        test_pause = test_pause if test_pause is not None else config.DEFAULT_TEST_PAUSE
        
        # Создаем результат со значениями по умолчанию
        result = {
            "success": False,
            "html": "",
            "error": "",
            "proxy": "",
            "user_agent": "",
            "html_path": "",
            "screenshot_path": ""
        }
        
        # Переносим блокирующие операции в отдельный поток, чтобы не блокировать event loop
        loop = asyncio.get_event_loop()
        
        try:
            # Запускаем инициализацию браузера в отдельном потоке
            await loop.run_in_executor(None, self.initialize_driver)
            
            # # Сохраняем информацию о прокси и user-agent
            # if config.USE_PROXY:
            #     result["proxy"] = str(self.current_proxy)
            # result["user_agent"] = self.current_user_agent
            
            # Строим URL для поиска
            search_url = self.build_search_url(
                query=query,
                domain=domain,
                num=num,
                gl=gl,
                hl=hl,
                lr=lr,
                cr=cr,
                location=location
            )
            logger.info(f"Поисковый URL: {search_url}")
            
            # Переходим по URL (блокирующая операция)
            await loop.run_in_executor(None, lambda: self.driver.get(search_url))

            # Обрабатываем диалоговое окно геолокации
            await loop.run_in_executor(None, self.handle_location_dialog)
            
            # Принимаем cookies
            await loop.run_in_executor(None, self.accept_cookies)
            
            # Ждем загрузку результатов
            await asyncio.sleep(random.uniform(*config.RANDOM_SLEEP_RANGE_MEDIUM))
            
            # Получаем исходный код страницы
            page_source = await loop.run_in_executor(None, lambda: self.driver.page_source)
            
            # Проверяем наличие капчи
            if self.check_for_captcha(page_source):
                error_msg = "Captcha on Google"
                logger.warning(error_msg)
                
                
                # Сохраняем HTML и скриншот с капчей, если установлен соответствующий флаг
                if config.SAVE_FAILED_RESULTS:
                    save_result = await loop.run_in_executor(
                        None, 
                        lambda: self.save_results(query, page_source, False, error_msg, test_pause)
                    )
                    result.update(save_result)
                
                result.update({
                    "success": False,
                    "error": error_msg,
                    "html": page_source 
                })
                
                return result
            
            # Сохраняем результаты
            save_result = await loop.run_in_executor(
                None, 
                lambda: self.save_results(query, page_source, True, "", test_pause)
            )
            
            # Обновляем результат
            result.update({
                "success": True,
                "html": page_source,
                **save_result
            })
            
            logger.info(f"Поисковый запрос '{query}' успешно выполнен")
            
        except Exception as e:
            error_msg = f"Ошибка при выполнении запроса: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            
        finally:
            # Закрываем браузер, если не задана пауза для тестирования
            if test_pause <= 0:
                await loop.run_in_executor(None, self.close_driver)
        
        return result


# Пример использования
async def main():
    """Пример использования GoogleRequester"""
    # Параметры запроса
    query = "order pizza delivery now"
    gl = "us"                     # локализация поиска
    hl = "en"                     # язык интерфейса
    domain = "google.com"         # домен Google
    num = 10                      # количество результатов
    location = None               # можно указать конкретное местоположение или None
    test_pause = config.DEFAULT_TEST_PAUSE  # пауза для тестирования из конфигурации
    
    requester = GoogleRequester()
    result = await requester.search_google_async(
        query=query,
        domain=domain,
        num=num,
        gl=gl,
        hl=hl,
        location=location,
        test_pause=test_pause
    )
    
    print(f"Успех: {result['success']}")
    if "html_path" in result:
        print(f"HTML сохранен в: {result['html_path']}")
    if "screenshot_path" in result:
        print(f"Скриншот сохранен в: {result['screenshot_path']}")
    
    if not result['success']:
        print(f"Ошибка: {result['error']}")

    return result

# if __name__ == "__main__":
#     # Запускаем асинхронную функцию
#     ans = asyncio.run(main())
#     print(ans.keys())