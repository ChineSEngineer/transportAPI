import json

from .base import ApiBase, ErrorCode, enum, time
from .transport import HttpTransport
from .transport import WebSocketTransport


class Encoding(enum.Enum):
  LPCM = 0
  OPUS = 1


class Layout(enum.Enum):
  NON_INTERLEAVED = 0
  INTERLEAVED = 1


class Endianness(enum.Enum):
  LITTLE = 0
  BIG = 1


class EventType(enum.Enum):
  ASR_ERROR = 0
  ASR_VAD_BEGIN = 1
  ASR_TEMP_RESULT = 2
  ASR_VAD_END = 3
  ASR_FINAL_RESULT=4


class AudioFormat(object):
  def __init__(self):
    self.encoding = Encoding.LPCM
    self.endianness = Endianness.LITTLE
    self.sampleRateHz = 16000
    self.sampleSizeInBits = 16
    self.numChannels = 1
    

class ApiAsr(ApiBase):
  def __init__(self, app_id, secret_key):
    ApiBase.__init__(self, app_id, secret_key)
    #TODO: customize port
    self.__http_client = HttpTransport()
    self.__ws_client = WebSocketTransport()
    self.__http_target = "http://api.soundai.cn/asr_non_streaming"
    self.__ws_target = "ws://api.soundai.cn/asr_streaming"
    self.__is_first_frame = True
    self.__connected = False


  def with_cb(self, cb):
    def wrapper(msg):
      json_obj = json.loads(msg)
      event = EventType.ASR_ERROR
      if json_obj.has_key("eof"):
        if json_obj["eof"] == 1:
          event = EventType.ASR_FINAL_RESULT
        else:
          event = EventType.ASR_TEMP_RESULT
      elif json_obj.has_key("vad_status"):
        if json_obj["vad_status"] == "begin":
          event = EventType.ASR_VAD_BEGIN
        if json_obj["vad_status"] == "end":
          event = EventType.ASR_VAD_END
      cb(event, msg)

    self.__ws_client.set_on_message(wrapper)
    return self

  
  def with_format(self, audio_format):
    self.__audio_format = audio_format
    return self


  #TODO: on_error
  def recognize(self, msg):
    if not self.__connected:
      asr_parameters=self._parameters(
        ('app_id', self._app_id),
        ('timestamp', self._timestamp())
      )
      asr_address = self.__ws_target + self._postfix("asr_streaming", asr_parameters, "")
      self.__ws_client.connect(asr_address)
      self.__connected = True

    if self.__is_first_frame:
      self.__ws_client.send(self.__create_websocket_header())
      self.__is_first_frame = False

    self.__ws_client.send(msg, True)


  def flush(self):
    self.__is_first_frame = True
    self.__ws_client.send("", True)


  def destroy(self):
    self.__ws_client.close()
    self.__connected = False


  def __create_websocket_header(self):
    if self.__audio_format.encoding == Encoding.OPUS:
      k_compress = "opus"
    else:
      k_compress = "none"

    json_map = {
      'audio' : {
          'channel' : self.__audio_format.numChannels,
          'compress' : k_compress,
          'format'  : 'pcm',
          'language' : 'zh',
          'rate' : self.__audio_format.sampleRateHz
      },
      'request' : {
          'appId' : self._app_id,
          'deviceId': 'deviceId_' + self._app_id,
          'dialogId': 'dialogId_' + str(int(time.time()*1000))
      }
    } 
    return json.dumps(json_map)


  def get_asr_result(self, data, audio_format):
    if not data or not self._app_id or not self._secret_key:
      return "", ErrorCode.CLOUD_ERROR_UNKNOWN_ERROR 

    asr_parameters=self._parameters(
      ('app_id', self._app_id),
      ('timestamp', self._timestamp())
    )
    asr_address = self.__http_target + self._postfix("asr_non_streaming", asr_parameters)

    if audio_format.encoding == Encoding.OPUS:
      content_type = "audio/opus;channel=" + str(audio_format.numChannels)
    else:
      content_type = "audio/pcm;channel=" + str(audio_format.numChannels)
    asr_header = {
      "Content-Type" : content_type,
      "Authorization" : "Basic aHk6N2Q3Mjc4ZWE0ZTc4NDIyYTk4YzEwODg4ODQyNWRhYjU="
    }
    conn = HttpTransport()
    ret = conn.send("POST", asr_address, data=data, headers = asr_header)
    return ret.content





