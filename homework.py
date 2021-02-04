from logging.handlers import RotatingFileHandler
import logging
import os
import requests
import time

from dotenv import load_dotenv
import telegram

# load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

PRAKTIKUM_BASE_URL = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
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
    homework_name = homework.get('homework_name')
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework.get('status') == 'reviewing':
        verdict = 'Работа взята на ревью.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        PRAKTIKUM_BASE_URL,
        params=params,
        headers=headers
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    tg_bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = int(time.time())
    current_timestamp = 0
    logging.debug('Бот успешно запущен. Наверное...')

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                msg_txt = parse_homework_status(
                    new_homework.get('homeworks')[0]
                )
                send_message(msg_txt, tg_bot)
                logging.info(f'Сообщение отправлено >>> {msg_txt}')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp
                                                 )
            time.sleep(5)

        except Exception as ex:
            msg_txt = f'Бот столкнулся с ошибкой: {ex}'
            print(msg_txt)
            logging.error(ex, exc_info=True)
            # Я не понял, как перегрузить logging.error для всех случаев
            # Поэтому отправку сообщений пишу здесь
            send_message(msg_txt, tg_bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
