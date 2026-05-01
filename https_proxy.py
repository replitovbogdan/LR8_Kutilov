import socket
import ssl
import threading
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HTTPSProxy:
    """Промежуточный прокси-контейнер: HTTPS → HTTP"""

    def __init__(self, cert_path, key_path, target_host, target_port, listen_port=8000):
        # Путь к SSL-сертификату
        self.cert_path = cert_path
        # Путь к приватному ключу
        self.key_path = key_path
        # Хост целевого приложения (Django)
        self.target_host = target_host
        # Порт целевого приложения (8000)
        self.target_port = target_port
        # Порт для приёма HTTPS-запросов (443)
        self.listen_port = listen_port

    def _forward_to_target(self, client_data, client_socket):
        """Пересылка запроса Django и возврат ответа клиенту"""
        try:
            # Разбор запроса: извлечение метода и пути
            lines = client_data.split(b'\r\n')
            first_line = lines[0].decode('utf-8', errors='replace')
            parts = first_line.split(' ')
            if len(parts) < 2:
                return
            method, path = parts[0], parts[1]

            # Создание сокета для соединения с Django
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_host, self.target_port))

            # Формирование запроса с добавлением заголовка X-Forwarded-Proto
            new_request = f"{method} {path} HTTP/1.1\r\n"
            new_request += f"Host: {self.target_host}\r\n"
            new_request += "X-Forwarded-Proto: https\r\n"
            new_request += "Connection: close\r\n\r\n"

            # Отправка запроса Django
            target_socket.send(new_request.encode('utf-8'))

            # Получение ответа от Django
            response = b''
            while True:
                chunk = target_socket.recv(4096)
                if not chunk:
                    break
                response += chunk
            target_socket.close()

            # Отправка ответа клиенту
            client_socket.send(response)

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\nProxy Error")

    def _handle_client(self, client_socket):
        """Обработка одного клиента"""
        try:
            # Получение данных от клиента
            data = client_socket.recv(8192)
            if data:
                self._forward_to_target(data, client_socket)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            client_socket.close()

    def start(self):
        """Запуск прокси-сервера"""
        # Создание TCP-сокета
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.listen_port))
        server_socket.listen(100)

        # Настройка SSL для поддержки HTTPS
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(self.cert_path, self.key_path)
        ssl_socket = context.wrap_socket(server_socket, server_side=True)

        logger.info(f"HTTPS прокси на порту {self.listen_port} -> http://{self.target_host}:{self.target_port}")

        # Основной цикл обработки соединений
        while True:
            try:
                client, addr = ssl_socket.accept()
                logger.info(f"Соединение от {addr}")
                # Запуск обработки клиента в отдельном потоке
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except KeyboardInterrupt:
                break

        ssl_socket.close()


def main():
    # Создание и запуск прокси-контейнера с параметрами по умолчанию
    proxy = HTTPSProxy(
        cert_path="cert.pem",
        key_path="key.pem",
        target_host="localhost",
        target_port=8000
    )
    proxy.start()


if __name__ == '__main__':
    main()