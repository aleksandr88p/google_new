# Google Search Requester

Асинхронный модуль для выполнения запросов к Google и получения HTML-страниц результатов поиска.
Использует undetected_chromedriver для обхода блокировок.

## Особенности

- Асинхронное выполнение запросов
- Обход блокировок Google с помощью undetected_chromedriver
- Поддержка прокси-серверов с аутентификацией
- Настраиваемые параметры поиска (домен, язык, количество результатов и т.д.)
- Сохранение HTML-страниц и скриншотов результатов
- Конфигурация вынесена в отдельный файл config.py

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

Все настройки находятся в файле `config.py`. Вы можете изменить их по своему усмотрению:

- Настройки прокси-серверов
- Параметры браузера Chrome
- Настройки сохранения результатов
- Список User-Agent для ротации
- Параметры поиска по умолчанию
- Настройки логирования

## Пример использования

```python
import asyncio
from page_requester import GoogleRequester

async def main():
    requester = GoogleRequester()
    result = await requester.search_google_async(
        query="ваш поисковый запрос",
        domain="google.com",
        num=10,
        gl="us",     # локализация поиска
        hl="en",     # язык интерфейса
        location=None  # можно указать конкретное местоположение
    )
    
    print(f"Успех: {result['success']}")
    if "html_path" in result:
        print(f"HTML сохранен в: {result['html_path']}")
    
    if not result['success']:
        print(f"Ошибка: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 