FROM python:3.11-slim

WORKDIR /app

# Копіюємо залежності та встановлюємо
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо вихідний код
COPY . .

EXPOSE 8080

CMD ["python", "run.py"]
