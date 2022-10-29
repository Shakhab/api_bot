import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from json import JSONDecodeError

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TIMEOUT = 5
BOT_TIMEOUT = 300


def parse_homework_status(homework):
    try:
        homework_name = homework.get('homework_name')
        status = homework.get('status')
    except KeyError:
        logging.exception(
            msg='Ключа "homework_name" либо "status" не найдено.')
        return None
    except Exception:
        logging.exception(msg='Что-то пошло не так как надо.')
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif status == 'approved':
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    else:
        verdict = 'Пришел непонятный статус homework'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {
        'from_date': current_timestamp
    }
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL, params=params, headers=headers)
        return homework_statuses.json()
    except JSONDecodeError:
        logging.exception(msg='Ошибка при восстановлении '
                              'Unicode данных в json')
    except UnicodeDecodeError:
        logging.exception(msg='Ошибка при восстановлении данных '
                              'из бит-последовательности')
    except requests.RequestException:
        logging.exception(msg='Ошибка соединения')
    except Exception:
        logging.exception(msg='Что-то сломалось:)')


def send_message(message, bot_client):
    return bot_client.send_message(CHAT_ID, message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get(
                'current_date', int(time.time()))
            time.sleep(BOT_TIMEOUT)

        except Exception as e:
            logging.exception(msg=f'Бот столкнулся с ошибкой: {e}')
            time.sleep(TIMEOUT)


if __name__ == '__main__':
    main()
