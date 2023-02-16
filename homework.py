import exceptions
import logging
import os
import requests
import sys
import time

from dotenv import load_dotenv
from http import HTTPStatus
from telegram import Bot, error


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

token_dict = {
    'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
}

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {token_dict["PRACTICUM_TOKEN"]}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения,
    которые необходимы для работы программы. 
    Если отсутствует хотя бы одна переменная окружения
    — продолжать работу бота нет смысла.
    """
    if all((PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)):
        return bool


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        logging.info('Сообщение подготовлено к отправке.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
    except Exception:
        raise error.TelegramError('Сообщение не отправлено.')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса. 
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API, 
    приведя его из формата JSON к типам данных Python
    """
    timestamp = timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info('Активирована get_api_answer.')
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if homework_statuses.status_code == HTTPStatus.OK:
            logging.info('Данные запрошены.')
            return homework_statuses.json()
        raise exceptions.RequestsError(
            f'Ошибка сервера: {ENDPOINT}, auth: {HEADERS}'
        )
    except Exception as error:
        raise f'Неизвестная ошибка: {error}'


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logging.info('Проверка данных запроса.')
    if not isinstance(response, dict):
        raise TypeError(f'Ответ является {type(response)}, а не словарем.')
    if response.get('homeworks') is None:
        raise KeyError('Ключа homeworks в словаре нет.')
    if type(response['homeworks']) == list and len(response['homeworks']) > 0:
        return response['homeworks']
    elif len(response['homeworks']) == 0:
        raise KeyError(f'Новых работ не обнаружено.')
    raise KeyError(f'{response["homeworks"]} некорректный список.')


def parse_status(homework):
    """Извлекает из информацию о статусе домашней работы."""
    logging.info('Парсинг статуса.')
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except Exception:
        raise KeyError(f'ключ не найден {homework}')
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    raise exceptions.StatusError('Неизвестный статус.')

# flake8: noqa: C901
def main():
    """Основная логика работы программы."""
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s - %(lineno)s',
        level=logging.INFO
    )
    if not check_tokens():
        TOKEN_error = []
        if not PRACTICUM_TOKEN:
            TOKEN_error.append('PRACTICUM_TOKEN')
        if not TELEGRAM_TOKEN:
            TOKEN_error.append('TELEGRAM_TOKEN')
        if not TELEGRAM_CHAT_ID:
            TOKEN_error.append('TELEGRAM_CHAT_ID')
        logging.critical(f'Не работает токен: {TOKEN_error}.')
        sys.exit()
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    message_old = 'Я начал свою работу.'
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            current_timestamp = int(time.time())
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
        finally:
            if message != message_old:
                send_message(bot, message)
            message_old = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
