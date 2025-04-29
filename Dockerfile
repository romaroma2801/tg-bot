# Используем официальный образ Python
FROM python:3.10-slim

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Команда запуска
CMD ["python", "nekuri_bot.py"]
