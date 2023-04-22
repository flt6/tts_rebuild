import asyncio
import re
from typing import Optional
import uuid
from datetime import datetime
from subprocess import PIPE, Popen
from time import time
import logging

import requests
from websockets.legacy import client
try:
    from rich import print
    from rich.logging import RichHandler
except ImportError:
    print("Rich is not available, please install it for more friendly output.")

token = None
_token_time = None
EXPIRE_TIME = 3550

log = logging.Logger("TTS")
log_handler = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
log.addHandler(log_handler)

def get_token(force_refresh:Optional[bool]=False) -> str:
    global token
    global _token_time
    now = time()
    if token is not None and\
        _token_time is not None \
        and _token_time - now < EXPIRE_TIME\
        and not force_refresh:
        return token
    _token_time = time()
    endpoint1 = "https://azure.microsoft.com/zh-cn/products/cognitive-services/speech-translation/"
    r = requests.get(endpoint1)
    r.raise_for_status()
    main_web_content = r.text
    token = re.search(r'token:\ "(.*)",', main_web_content)
    assert token is not None
    token = token.group(1)
    return token

# Generate X-Timestamp all correctly formatted
def _getXTime():
    hr_cr = lambda hr: str((hr - 1) % 24)
    fr = lambda x: ":".join(["%02d" % int(i) for i in str(x).split(':')])

    now = datetime.now()
    n = [
        fr(now.year), fr(now.month), fr(now.day), fr(hr_cr(int(now.hour))),
        fr(now.minute), fr(now.second), str(now.microsecond)[:3]
    ]
    return "{}-{}-{}T{}:{}:{}.{}Z".format(*n)

async def implete(SSML_text:str,opt_fmt:str,debug:bool,method:int=1) -> tuple[bool,str,bytes]:
    '''
        Insider function.

        You should use `speech.SpeechSynthesizer` instead of this function
    '''
    method = 2
    log_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    req_id = uuid.uuid4().hex.upper()
    log.debug("method=%d" % method)
    if method == 1:
        try:
            Auth_Token = get_token()
            endpoint2 = "wss://eastus.tts.speech.microsoft.com/cognitiveservices/websocket/v1?Authorization=" + \
                Auth_Token + "&X-ConnectionId=" + req_id
            headers = {}
        except requests.exceptions.HTTPError as e:
            log.error("(token)The azure server response not 200")
            raise e
        except requests.exceptions.RequestException as e:
            log.error("Can't get token due to the network reason. Please retry.")
            raise e
        except Exception as e:
            log.error("An unexpected exception occurred. If this error kept going, please make an Issue on github with code 1")
            log.info("We will use the backup method.")
            log.debug("RE",exc_info=e)
            return await implete(SSML_text,opt_fmt,debug,2)
    elif method == 2:
        endpoint2 = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
        # headers = {'Origin':'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold'}
        if opt_fmt != "audio-24khz-48kbitrate-mono-mp3":
            log.warning("Only type `audio-24khz-48kbitrate-mono-mp3` is allowed.")
        if SSML_text.count("</voice>")>=2:
            raise ValueError("Mutiple <voice> tag is not supported.")
        headers = {
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Origin": "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41"
        }
    else:
        raise ValueError(f"Method must between 1 to 3, but '{method}' got. If you haven't specified 'method', this is because of all the methods failed. If so, please make an Issue.")
    
    log.debug("Prepare (%s)" % req_id)

    try:
        async with client.connect(endpoint2,extra_headers=headers) as websocket:
            log.debug("Connect (%s)"% req_id)
            message_1 = \
                f"X-Timestamp:{_getXTime()}\r\n"\
                "Content-Type:application/json; charset=utf-8\r\n"\
                "Path:speech.config\r\n"\
                "\r\n"\
                '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":false,"wordBoundaryEnabled":false},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}'
            await websocket.send(message_1)

            message_2 = \
                f"X-RequestId:{req_id}\r\n"\
                "Content-Type:application/ssml+xml\r\n"\
                f"X-Timestamp:{_getXTime()}Z\r\n"\
                "Path:ssml\r\n\r\n"\
                f"{SSML_text}"
            await websocket.send(message_2)

            audio_stream:bytes = b''
            while(True):
                response = await websocket.recv()
                # print(str(response))
                if "Path:turn.end" not in str(response):
                    if type(response) == type(bytes()):
                        try:
                            needle = b'Path:audio\r\n'
                            start_ind = response.find(needle) + len(needle) # type: ignore
                            audio_stream += response[start_ind:] # type: ignore
                        except:
                            log.warning("A part of the audio parsed failed!")
                else:
                    break
            log.debug("end ({})".format(req_id))
            return req_id, audio_stream
    except Exception as e:
        log.error("An unexpected exception occurred. If this error kept going, please make an Issue on github with code %d"%method)
        log.info("We will use the backup method.")
        log.debug("Error",exc_info=e)
        return await implete(SSML_text,opt_fmt,debug,method+1)


class Test:
    def __init__(self,SSML_text:str):
        task = self.createTask(SSML_text)
        task.add_done_callback(self._callback)
        asyncio.get_event_loop().run_until_complete(task)
    def createTask(self,SSML_text:str) -> asyncio.Task:
        return asyncio.get_event_loop().create_task(implete(SSML_text,"audio-16khz-32kbitrate-mono-mp3",True))
    def _callback(self,future:asyncio.Future):
        ret = future.result()
        _,b = ret
        with open('output.mp3',"wb") as f:
            f.write(b)

if __name__ == "__main__":
    SSML_text = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        wss的v1 接口目
    </voice>
</speak>'''
    t = Test(SSML_text)
