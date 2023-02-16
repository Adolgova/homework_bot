import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot
from http import HTTPStatus
from json import JSONDecodeError

from exceptions import NoTokenException, NoResponceException, MessageException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger('__name__')


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение успешно отправлено в Telegram')
    except MessageException as error:
        logger.error(f'Ошибка при отправке сообщения. {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = timestamp or int(time.time())
    params = {'from_date': timestamp}
    request = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if request.status_code != HTTPStatus.OK:
        logger.error(
            'Код статуса ответа API отличается от ожидаемого'
        )
        raise NoResponceException(
            'Код статуса ответа API отличается от ожидаемого'
        )
    try:
        homework_statuses = request.json()
    except JSONDecodeError:
        logger.error('Ответ не преобразуется в JSON')
        raise JSONDecodeError('Ответ не преобразуется в JSON')
    except ConnectionError as error:
        logger.error(f'Ошибка при запросе к API: {error}')
    return homework_statuses


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logger.error(
            'Формат ответа API отличается от ожидаемого'
        )
        raise TypeError(
            'Формат ответа API отличается от ожидаемого'
        )
    homeworks = response.get('homeworks')
    if homeworks is None:
        logger.error(
            'Ответ API не содержит ключ homeworks'
        )
        raise KeyError(
            'Ответ API не содержит ключ homeworks'
        )
    if isinstance(homeworks, list):
        if homeworks == []:
            logger.debug('В ответе нет новых статусов')
    else:
        logger.error(
            'Тип значения домашнего задания отличается от ожидаемого'
        )
        raise TypeError(
            'Тип значения домашнего задания отличается от ожидаемого'
        )
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error(
            'Недокументированный статус домашней работы'
        )
        raise KeyError(
            'Недокументированный статус домашней работы'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    check = all([
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ])
    return check


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise NoTokenException(
            'Одна или более необходимых переменных отсутствуют в окружении'
        )
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks_ok = check_response(response)
            if homeworks_ok:
                send_message(bot, parse_status(homeworks_ok[0]))
            timestamp = response.get('current_date', timestamp)
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
