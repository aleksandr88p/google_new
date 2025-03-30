FROM python:3.9-slim

# Установка Chrome и зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    unzip \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование требований и установка зависимостей
COPY api2_V_2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install python-dotenv fastapi uvicorn beautifulsoup4 lxml

# Копирование кода приложения
COPY api2_V_2/ .

# Создание директорий для сохранения результатов
RUN mkdir -p results screenshots counter_data

# Запуск API сервера
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]