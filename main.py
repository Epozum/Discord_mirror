import requests
import websocket
import json
import threading
from pymongo import MongoClient
import time

checker_token = "*************************************"


def main_func():
    try:
        f = open('../config.json', 'r')  # file with channels to scan
        channels_data = json.load(f)

        user_token = channels_data["user_token"]

        def send_json_request(ws, request):
            ws.send(json.dumps(request))

        def receive_json_response(ws):
            response = ws.recv()
            if response:
                return json.loads(response)

        def get_attachment_media(media):  # getting attachment madia
            media_array = []
            for i in media:
                response = i['url']
                media_array.append(response)
            return media_array

        def get_channel(id_channel):
            for i in channels_data['channels_data']:
                if i['from_chat_id'] == id_channel:
                    return i['to_chat_id']
            return False

        def heartbeat(interval, ws):  # heartbeat function which keeps connection to WebSocket
            print("Heartbeat begin")
            while True:
                time.sleep(interval)
                heartbeat_json = {
                    "op": 1,
                    "d": "null"
                }
                send_json_request(ws, heartbeat_json)
                print("Heartbeat sent")

        # WebSocket
        ws = websocket.WebSocket()
        ws.connect("wss://gateway.discord.gg/?v=6&encording=json")
        event = receive_json_response(ws)

        heartbeat_interval = event['d']['heartbeat_interval'] / 1000
        threading._start_new_thread(heartbeat, (heartbeat_interval, ws))

        payload = {
            'op': 2,
            "d": {
                "token": user_token,
                "properties": {
                    "$os": 'linux',
                    "$browser": 'chrome',
                    "$device": 'pc'
                }
            }
        }

        send_json_request(ws, payload)

        # Database initialization
        cluster = MongoClient("mongodb://localhost:27017")
        db = cluster[channels_data["database_cluster"]]
        collection = db[channels_data["database_collection"]]

        # Main functional
        while True:
            event = receive_json_response(ws)
            try:
                if event['d']['author']['id'] != '10293134896820*****':
                    id_channel = event['d']['channel_id']
                    to_chat = get_channel(id_channel)
                    if to_chat:

                        if event['d']['referenced_message'] is None:
                            reply_id = None
                        else:
                            reply_id = event['d']['referenced_message']['id']

                        attachment_media = get_attachment_media(event['d']['attachments'])
                        post = {"message_id": event['d']['id'],
                                "reply_id": reply_id,
                                "content": event['d']['content'],
                                "to_chat_id": to_chat,
                                "attachments": attachment_media,
                                "is_checked": False,
                                "embeds": event['d']['embeds'],
                                "username": event['d']['author']['username']}
                        collection.insert_one(post)

                        print(f"{event['d']['author']['username']}::{event['d']['content']}::{attachment_media}")

                    op_code = event('op')
                    if op_code == 11:
                        print('Heartbeat recieved')
            except:
                pass

    except Exception as e:
        print("Main Function: ")
        print(e)
        checker_function()
        main_func()
        try:
            r = requests.get(
                "https://****************************************", params={
                    "message": "Main Function: " + str(e),
                    "token": checker_token
                })
        except:
            pass
        pass


# Sending error messages to admin panel
def checker_function():
    try:
        r = requests.get("https://****************************************" + checker_token)
        sec = (int(r.text))
        if sec == -1:
            return

        def func_wrapper():
            checker_function()

        t = threading.Timer(sec, func_wrapper)
        t.start()
    except Exception as e:
        print("CheckerFunction Function: ")
        print(e)


if __name__ == '__main__':
    checker_function()
    main_func()
