import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (APIAnswerNot200Error, NoneDocumentStatusError,
                        RequestError,
                        )

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
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)


def check_tokens():
    """Проверка доступности переменных окружения."""
    logger.debug('Проверка наличия токенов')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщений в Telegram."""
    try:
        logger.debug('Начало отправления сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logger.error(
            f'При отправке сообщения произошёл сбой: {error}'
        )
    else:
        logger.debug(
            f'Бот успешно отправил сообщение: "{message}"'
        )


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    payload = {
        'from_date': timestamp,
    }
    logger.debug(f'Начало запроса к API: {ENDPOINT}')
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
    except Exception as error:
        error_message = (
            f'Произошел сбой при запросе к API: {error}'
            f'Запрос был таким: {ENDPOINT}, {HEADERS}, {payload}'
        )
        logger.error(error_message)
        raise RequestError(error_message)
    else:
        logger.debug('Запрос был успешно отправлен')
    if response.status_code != HTTPStatus.OK:
        error_message = (
            f'Эндпоинт {ENDPOINT} недоступен.'
            f'Код ответа API: {response.status_code}'
        )
        logger.error(error_message)
        raise APIAnswerNot200Error(error_message)
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие."""
    if not isinstance(response, dict):
        raise TypeError('Неправильный тип данных у объекта response')
    if not response.get('homeworks'):
        error_message = 'Отсутствуют ожидаемые ключи в ответе API'
        logger.error(error_message)
        raise KeyError(error_message)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неправильный тип данных у объекта homeworks')
    return homeworks[0]


def parse_status(homework):
    """Получение статуса проверки работы."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status is None:
        raise KeyError('Пустое значение homework_status')
    if homework_name is None:
        raise KeyError('Пустое значение homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        error_message = (
            f'Неожиданный статус домашней работы: {homework_status}'
        )
        logger.error(error_message)
        raise NoneDocumentStatusError(error_message)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = 'Программа была остановлена из за отсутствия токенов'
        logger.critical(error_message)
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    start_message = 'DomashkaBot начал свою работу'
    logger.info(start_message)
    send_message(bot, start_message)
    timestamp = int(time.time())
    past_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message != past_message:
                send_message(bot, message)
                past_message = message
            else:
                logger.debug('Отсутствуют в ответе новые статусы')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != past_message:
                send_message(bot, message)
                past_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - [%(levelname)s] - %(message)s',
    )
    try:
        main()
    except KeyboardInterrupt:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        end_message = 'DomashkaBot закончил свою работу'
        logger.info(end_message)
        send_message(bot, end_message)
