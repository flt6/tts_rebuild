from mytts import SpeechConfig, AudioOutputConfig, SpeechSynthesizer
from mytts import ResultReason, CancellationErrorCode
from os import remove
import pytest
try:
    from rich import print
except ImportError:
    pass

class Test:
    SSML_text = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
        <voice name="zh-CN-XiaoxiaoNeural">
            wss的v1 接口目
        </voice>
    </speak>'''
    text = "123456"
    def test_speak_ssml(self):
        speech_cfg = SpeechConfig()
        audio_cfg = AudioOutputConfig(filename="opt1.mp3")
        syn = SpeechSynthesizer(speech_cfg,audio_cfg,debug=True)
        self.check(syn.speak_ssml(self.SSML_text))
    def test_speak_text(self):
        speech_cfg = SpeechConfig()
        audio_cfg = AudioOutputConfig(filename="opt2.mp3")
        syn = SpeechSynthesizer(speech_cfg,audio_cfg,debug=True)
        self.check(syn.speak_text(self.text))
    def test_speak_ssml_async(self):
        speech_cfg = SpeechConfig()
        audio_cfg = AudioOutputConfig(filename="opt3.mp3")
        syn = SpeechSynthesizer(speech_cfg,audio_cfg,debug=True)
        t = syn.speak_ssml_async(self.SSML_text)
        self.check(t.get())
        
    def test_speak_text_async(self):
        speech_cfg = SpeechConfig()
        audio_cfg = AudioOutputConfig(filename="opt4.mp3")
        syn = SpeechSynthesizer(speech_cfg,audio_cfg,debug=True)
        t = syn.speak_text_async(self.text)
        self.check(t.get())
    def check(self,rst):
        if rst.reason!=ResultReason.SynthesizingAudioCompleted:
            print("Error")
            print("Reason",rst.reason)
            if rst.reason==ResultReason.Canceled:
                detail = rst.cancellation_details
                assert detail is not None
                print("Detail:")
                print("error code:",detail.error_code)
                print("error reason:",detail.reason)
                if detail.error_code == CancellationErrorCode.RuntimeError:
                    print("Traceback Information")
                    print(detail.exception)
                    raise RuntimeError(str(detail.exception))

@pytest.fixture
def cleanup():
    def rm():
        remove("opt1.mp3")
        remove("opt2.mp3")
        remove("opt3.mp3")
        remove("opt4.mp3")
    rm()
    yield
    rm()
if __name__ == "__main__":
    test = Test()
    test.test_speak_text_async()
    test.test_speak_ssml_async()
    test.test_speak_text()
    test.test_speak_ssml()
   