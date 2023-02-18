import asyncio
import json
import os

import uvicorn
import yaml
from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel
from revChatGPT.V1 import Chatbot

try:
    from .chat_logger import ChatLogger
except ImportError:
    from chat_logger import ChatLogger


class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    chatName: str = 'Master'
    groupId: int = -1
    timestamp: int = -1
    signature: str = ''
    returnVoice: bool = False


semaphore = asyncio.Semaphore(1)  # concurrency limit is 1

os.chdir(os.path.dirname(os.path.abspath(__file__)))
workdir = os.getcwd()
logger.info(f"workdir:{workdir}")

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    bot = Chatbot(config, conversation_id=None)

with open("config.yaml", "r", encoding="utf-8") as f:
    apicfg = yaml.safe_load(f)

app = FastAPI()
chat_logger = ChatLogger(os.path.join(workdir, "conversations"), "chatgpt")


# HelloWorld
@app.get('/')
def read_root():
    return {'HelloWorld': 'ChatGPT-HTTPAPI'}


@app.post('/{command}')
# @retry.retry(tries=3, delay=3)
async def universalHandler(command=None, body: ReqBody = None):
    global bot
    global semaphore
    async with semaphore:
        if command is None:
            command = ['chat', 'forgetme', 'history']
        # msg = newMsg(body, command)
        prompt: str = body.chatText
        finalMsg: str

        logger.info(f"prompt: {prompt}")
        if command == 'chat':
            for data in bot.ask(prompt):
                finalMsg = data["message"]
            chat_logger.record_conversation(f"conversation id:{bot.conversation_id}\n"
                                            f"you: {prompt}\n"
                                            f"bot: {finalMsg}\n")
            logger.info(f"chat: finalMsg: {finalMsg}")
        elif command == 'forgetme':
            bot.reset_chat()
            chat_logger.start_new_conversation()
            finalMsg = "已重置对话"  # Reset conversation
            logger.info(f"forgetme: finalMsg: {finalMsg}")
        elif command == 'history':
            finalMsg = bot.get_msg_history(bot.conversation_id)
            logger.info(f"history: finalMsg: {finalMsg}")
        else:
            finalMsg = "未知命令"  # Unknown command
            logger.info(f"unknown command: finalMsg: {finalMsg}")
        return {'success': True, 'response': finalMsg}


@app.post('/rollback/{num}')
async def rollback(num: int):
    global bot
    global semaphore
    async with semaphore:
        bot.rollback_conversation(num)
        logger.info(f"rollback: {num} conversations")
        chat_logger.record_conversation(f"回退{num}条对话\n")
        return {'success': True, 'response': f"已回退{num}条对话"}


### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    uvicorn.run('main:app', host=apicfg['uvicorn_host'], port=apicfg['uvicorn_port'],
                reload=False, log_level=apicfg['uvicorn_loglevel'],
                workers=apicfg['uvicorn_workers'])
