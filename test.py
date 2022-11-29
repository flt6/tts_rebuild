from mytts import SpeechConfig, AudioOutputConfig, SpeechSynthesizer
from mytts import ResultReason, CancellationErrorCode
from rich import print

speech_cfg = SpeechConfig()
audio_cfg = AudioOutputConfig(filename="opt.mp3")
syn = SpeechSynthesizer(speech_cfg,audio_cfg,debug=True)
SSML_text = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        wss的v1 接口目
    </voice>
</speak>'''
# syn.speak_ssml(SSML_text)
syn.speak_text_async('''秦孝公据崤函之固，拥雍州之地，君臣固守以窥周室，有席卷天下，包举宇内，囊括四海之意，并吞八荒之心。当是时也，商君佐之，内立法度，务耕织，修守战之具；外连衡而斗诸侯。于是秦人拱手而取西河之外。''')
syn.speak_text_async("websocket2 filename")
a=syn.speak_text_async("websocket3 filename")
rst = a.get()
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