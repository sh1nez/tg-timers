import toml
import asyncio
from datetime import datetime
from datetime import timedelta
from pyrogram import types, Client
import pyrogram.errors
import string
import random

try:
    with open('config.toml', 'r') as config_file:
        config_data = toml.load(config_file)
except FileNotFoundError as e:
    exit(e)

api_hash = config_data["api_hash"]
api_id = int(config_data["api_id"])
chat_id = int(config_data["chat_id"])
extra_message = config_data["extra_message"]
end_message = config_data["end_message"]
sleep_time = config_data["sleep_time"]
event_date = datetime.strptime(config_data["end_date"], "%Y-%m-%dT%H:%M:%S")

if "sleep_time" not in config_data:
    sleep_time = 5


def update_config():
    with open("config.toml", "w") as file:
        toml.dump(config_data, file)


def new_message():
    pass


async def update_pin_message(app):
    global message_id
    await app.delete_messages(chat_id=chat_id, message_ids=[message_id], revoke=True)
    new_message = await app.send_message(chat_id=chat_id, text="init")
    await new_message.pin(both_sides=True)
    config_data["message_id"] = new_message.id
    message_id = new_message.id
    update_config()


def dayword(n: int):
    if n == 0:
        return ""
    tmp = n % 10
    text = ""
    if n in range(11, 15):
        text = "дней"
    if tmp == 1:
        text = "день"
    elif tmp > 1 and tmp < 5:
        text = "дня"
    else:
        text = "дней"
    return str(n) + " " + text + " "


def hourword(n: int):
    if n == 0:
        return ""
    text = "часов"
    if n in range(11, 15):
        text = "часов"
    tmp = n % 10
    if tmp == 1:
        text = "час"
    if tmp > 1 and tmp < 5:
        text = "часа"
    return str(n) + " " + text + " "


def min_sec_add(n: int):
    tmp = n % 10
    if n in range(11, 15):
        return ""
    if tmp == 1 and n != 11:
        return "а"
    elif tmp > 1 and tmp < 5:
        return "ы"
    return ""


def minword(n: int):
    if n == 0:
        return ""
    return str(n) + " минут" + min_sec_add(n) + " "


def secword(n: int):
    if n == 0:
        return ""
    return str(n) + " секунд" + min_sec_add(n)


def parse_date_int(time_input):
    if isinstance(time_input, datetime):
        days = 0
        hours = time_input.hour
        minutes = time_input.minute
        seconds = time_input.second
    elif isinstance(time_input, timedelta):
        days = time_input.days
        hours, remainder = divmod(time_input.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

    else:
        raise TypeError("Wrong type: only datetime or timedelta")
    return (days, hours, minutes, seconds)


def date_to_text(time_left: datetime):
    days, hours, minutes, seconds = parse_date_int(time_left)
    return f"{dayword(days)}{hourword(hours)}{minword(minutes)}{secword(seconds)}"


def genereate_seed():
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(16))


evenet_text = date_to_text(event_date)

app = Client("my_account", api_id, api_hash)

seed = genereate_seed()
print(f"send message with seed phrase to start timer!\n{seed}")


fl = 0


@app.on_message(pyrogram.filters.text)
async def check_message(client, message: types.Message):
    global seed, fl, message_id, chat_id, config_data
    if fl > 0:
        return
    if message.text == seed:  # TODO
        fl += 1
        seed = genereate_seed()
        print(f"In the future you can add multiple timers with a new seed:\n{seed}")

        chat_id = message.chat.id
        message_id = message.id

        config_data["message_id"] = message.id
        config_data["chat_id"] = message.chat.id

        update_config()
        await main()


async def main():
    while 1:
        time_left = event_date - datetime.now()
        if time_left.total_seconds() <= 0:
            ms = await app.send_message(chat_id=chat_id, text=end_message)
            await ms.pin()
            exit()
        try:
            text = "Осталось: " + \
                date_to_text(time_left) + " " + extra_message
            await app.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        except pyrogram.errors.exceptions.bad_request_400.MessageEditTimeExpired:
            await update_pin_message(app)
        await asyncio.sleep(sleep_time)

app.run()
