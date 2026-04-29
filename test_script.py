
import pika
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('RABBIT_USER',)
password = os.getenv('RABBIT_PASS',)

print(f'Попытка подключения с {username}:{password}')

try:
    credentials = pika.PlainCredentials(username, password)
    params = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials
    )
    connection = pika.BlockingConnection(params)
    print('Успешное подключение к RabbitMQ!')
    connection.close()
except Exception as e:
    print(f'✗ Ошибка: {e}')