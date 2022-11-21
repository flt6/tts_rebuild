from mytts import SpeechConfig, AudioOutputConfig, SpeechSynthesizer

speech_cfg = SpeechConfig()
audio_cfg = AudioOutputConfig(filename="opt.mp3")
syn = SpeechSynthesizer(speech_cfg,audio_cfg)
SSML_text = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        wss的v1 接口目
    </voice>
</speak>'''
# syn.speak_ssml(SSML_text)
syn.speak_text("websocket filename")