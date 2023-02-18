# coding:utf-8

import json
import time

import requests
from pydantic import BaseModel


class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    chatName: str = 'Master'
    groupId: int = -1
    timestamp: int = -1
    signature: str = ''
    returnVoice: bool = False


prompt = "tell us a story"


def generate_post_body(chatText: str, chatId: int, groupId: int, additional_info: dict = {}):
    def get_unix_time():
        return int(time.time())

    return json.dumps(
        {
            "chatText": chatText,
            "chatId": str(chatId),
            "groupId": str(groupId),
            "signature": "no sign",
            "timestamp": str(get_unix_time()),
        } | additional_info
    ).encode('utf-8')


api_url = "http://localhost:2335/chat"

body = generate_post_body(prompt, 123, 456)

response = requests.post(api_url, data=body)

print(response.text)

print('done')
