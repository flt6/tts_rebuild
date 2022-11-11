class AudioOutputConfig():
    """
    Represents specific audio configuration, such as audio output device, file, or custom audio streams

    Generates an audio configuration for the speech synthesizer. Only one argument can be
    passed at a time.

    :param use_default_speaker: Specifies to use the system default speaker for audio
        output.
    :param filename: Specifies an audio output file. The parent directory must already exist.
    :param stream: Creates an AudioOutputConfig object representing the specified stream.
    :param device_name: Specifies the id of the audio device to use.
         This functionality was added in version 1.17.0.
    """

    def __init__(self, use_default_speaker: bool = False, filename: str = None,
                 stream: AudioOutputStream = None, device_name: str = None):
        if not isinstance(use_default_speaker, bool):
            raise ValueError('use_default_speaker must be a bool, is "{}"'.format(
                use_default_speaker))
        handle = _spx_handle(0)
        if filename is None and stream is None and device_name is None:
            if use_default_speaker:
                _call_hr_fn(fn=_sdk_lib.audio_config_create_audio_output_from_default_speaker, *[ctypes.byref(handle)])
            else:
                raise ValueError('default speaker needs to be explicitly activated')
        else:
            if sum(x is not None for x in (filename, stream, device_name)) > 1:
                raise ValueError('only one of filename, stream, and device_name can be given')

            if filename is not None:
                c_filename = _c_str(filename)
                _call_hr_fn(fn=_sdk_lib.audio_config_create_audio_output_from_wav_file_name, *[ctypes.byref(handle), c_filename])
            elif stream is not None:
                self._stream = stream
                _call_hr_fn(fn=_sdk_lib.audio_config_create_audio_output_from_stream, *[ctypes.byref(handle), stream._handle])
            elif device_name is not None:
                c_device = _c_str(device_name)
                _call_hr_fn(fn=_sdk_lib.audio_config_create_audio_output_from_a_speaker, *[ctypes.byref(handle), c_device])
            else:
                raise ValueError('cannot construct AudioOutputConfig with the given arguments')
        self.__handle = _Handle(handle, _sdk_lib.audio_config_is_handle_valid, _sdk_lib.audio_config_release)

    @property
    def _handle(self) -> _spx_handle:
        return self.__handle.get()
