import asyncio
import uuid
from datetime import datetime
import logging

from requests import post
from json import dumps
from websockets.legacy import client
try:
    from rich import print
    from rich.logging import RichHandler
except ImportError:
    print("Rich is not available, please install it for more friendly output.")

log = logging.Logger("TTS")
log_handler = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
log.addHandler(log_handler)

class InvalidRequest(RuntimeError):
    def __init__(self, msg, innerError):
        self.msg = msg
        self.innerError = innerError
    def __repr__(self) -> str:
        return f"msg: %s" % self.msg
    def __rich_repr__(self):
        yield self.msg
        yield self.innerError
    def __str__(self) -> str:
        return self.__repr__()

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
    log_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    req_id = uuid.uuid4().hex.upper()
    log.debug("method=%d" % method)
    if method == 1:
        url = "https://southeastasia.api.speech.microsoft.com/accfreetrial/texttospeech/acc/v3.0-beta1/vcg/speak"
        headers = {
            "origin": "https://speech.microsoft.com",
            "content-type": "application/json"
        }
        data = {
            "ssml": SSML_text,
            "ttsAudioFormat": opt_fmt,
            # "offsetInPlainText": 2,
            # "lengthInPlainText": 8
        }
        try:
            log.debug(f"Connected ({req_id})")
            ret = post(url,data=dumps(data),headers=headers)
            log.debug(f"End ({req_id})")
            code = ret.status_code
            if code == 200:
                return req_id, ret.content
            elif code == 400:
                data = ret.json()
                if "TtsAudioFormat" in data["message"]:
                    raise ValueError(data["message"])
                raise InvalidRequest(data["message"],data["innerError"])
            else:
                raise RuntimeError(data)
        except Exception as e:
            log.error("An unexpected exception occurred. If this error kept going, please make an Issue on github with code 1")
            log.info("We will use the backup method.")
            log.debug("RE",exc_info=e)
            return await implete(SSML_text,opt_fmt,debug,2)
    elif method == 2:
        url = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
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
        
        log.debug("Prepare (%s)" % req_id)

        try:
            async with client.connect(url,extra_headers=headers) as websocket:
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
    else:
        raise ValueError(f"Method must between 1 to 2, but '{method}' got. If you haven't specified 'method', this is because of all the methods failed. If so, please make an Issue.")


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
