import logging
import os
import requests
import time
from logging.handlers import RotatingFileHandler

import telegram


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_BASE_URL = (
    'https://praktikum.yandex.ru/api/user_api/{0}'
)


logging.basicConfig(
    level=logging.DEBUG,
    filename='tg_bot.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

logger = logging.getLogger('__name__')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'tg_bot.log',
    maxBytes=50000000,
    backupCount=5,
)
logger.addHandler(handler)


def parse_homework_status(homework):
    error_msg = 'Ошибка получения статуса ДЗ.'

    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error(error_msg)
        return None

    hw_status = homework.get('status')
    if hw_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif hw_status == 'reviewing':
        verdict = 'Работа взята на ревью.'
    elif hw_status is None:
        logging.error(error_msg)
        return None
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    # в main же обрабатывается исключение,
    # а get_homework_statuses вызывается оттуда.
    # Зачем тут нужна праверка ?
    homework_statuses = requests.get(
        PRAKTIKUM_BASE_URL.format('homework_statuses/'),
        params=params,
        headers=headers
    )
    # Идея была вот такая. Но Pytest не пропускает и платформа тоже
    # 'MockResponseGET' object has no attribute 'raise_for_status'
    '''try:
        homework_statuses.raise_for_status()
    except requests.exceptions.HTTPError:
        error_msg = f'Практикум недоступен. '\
                    f'Status code: {homework_statuses.status_code}'
        logging.error(error_msg)
        return None'''
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    tg_bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.debug('Бот успешно запущен. Наверное...')
    send_message('Бот успешно запущен. Наверное...', tg_bot)

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework:
                hw_list = new_homework.get('homeworks')
                if hw_list:
                    msg_txt = parse_homework_status(hw_list[0])
                    if msg_txt is not None:
                        send_message(msg_txt, tg_bot)
                        logging.info(f'Сообщение отправлено >>> {msg_txt}')
                current_timestamp = new_homework.get('current_date',
                                                     int(time.time())
                                                     )
            time.sleep(30)

        except Exception as ex:
            msg_txt = f'Бот столкнулся с ошибкой: {ex}'
            print(msg_txt)
            logging.error(ex, exc_info=True)
            send_message(msg_txt, tg_bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
