import asyncio
import re
from typing import Optional
import uuid
from datetime import datetime
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
    token_expr = re.compile('token: \"(.*?)\"', re.DOTALL)
    token = re.findall(token_expr, main_web_content)[0]
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

async def implete(SSML_text:str,opt_fmt:str,debug:bool,method:int=1) -> tuple[str,bytes]:
    '''
        Insider function.

        You should use `speech.SpeechSynthesizer` instead of this function
    '''
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
        endpoint2 = f"wss://eastus.api.speech.mic4rosoft.com/cognitiveservices/websocket/v1?TrafficType=AzureDemo&Authorization=bearer%20undefined&X-ConnectionId={req_id}"
        headers = {'Origin':'https://azure.microsoft.com'}
    elif method == 3:
        endpoint2 = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
        headers = {'Origin':'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold'}
        if opt_fmt!="webm-24khz-16bit-mono-opus":
            opt_fmt = "webm-24khz-16bit-mono-opus"
            log.warning("method to 3, only 'webm-24khz-16bit-mono-opus' is supported.")
    else:
        raise ValueError(f"Method must between 1 to 3, but '{method}' got. If you haven't specified 'method', this is because of all the methods failed. If so, please make an Issue.")
    
    log.debug("Prepare (%s)" % req_id)

    try:
        async with client.connect(endpoint2,extra_headers=headers) as websocket:
            log.debug("Connect (%s)"% req_id)
            payload_1 = '{"context":{"system":{"name":"SpeechSDK","version":"1.12.1-rc.1","build":"JavaScript","lang":"JavaScript","os":{"platform":"Browser/Linux x86_64","name":"Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0","version":"5.0 (X11)"}}}}'
            message_1 = 'Path : speech.config\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + \
                _getXTime() + '\r\nContent-Type: application/json\r\n\r\n' + payload_1
            await websocket.send(message_1)

            payload_2 = '{"synthesis":{"audio":{"metadataOptions":{"sentenceBoundaryEnabled":false,"wordBoundaryEnabled":false},"outputFormat":"%s"}}}'%opt_fmt
            message_2 = 'Path : synthesis.context\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + \
                _getXTime() + '\r\nContent-Type: application/json\r\n\r\n' + payload_2
            await websocket.send(message_2)

            payload_3 = SSML_text
            message_3 = 'Path: ssml\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + \
                _getXTime() + '\r\nContent-Type: application/ssml+xml\r\n\r\n' + payload_3
            await websocket.send(message_3)

            end_resp_pat = re.compile('Path:turn.end')
            audio_stream:bytes = b''
            while(True):
                response = await websocket.recv()
                if re.search(end_resp_pat, str(response)) is None:
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
        return req_id,audio_stream
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
        print(ret)
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
