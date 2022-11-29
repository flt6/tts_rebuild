from .speech import *

from .enums import (
    CancellationErrorCode,
    CancellationReason,
    ResultReason,
)
from .speech import (
    ResultFuture,
    SpeechSynthesisCancellationDetails,
    SpeechSynthesisResult,
    SpeechConfig,
    AudioOutputConfig,
    SpeechSynthesizer
)
audio = speech

root_namespace_classes = (
    CancellationErrorCode,
    CancellationReason,
    ResultFuture,
    ResultReason,
    SpeechConfig,
    SpeechSynthesisCancellationDetails,
    SpeechSynthesisOutputFormat,
    SpeechSynthesisResult,
    SpeechSynthesizer,
)
for cls in root_namespace_classes:
    cls.__module__ = __name__
__all__ = [cls.__name__ for cls in root_namespace_classes]
