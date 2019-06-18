import json

from .base import ApiBase, ErrorCode, enum
from .transport import HttpTransport


class AudioType(enum.Enum):
  LPCM = 0,
  MPEG = 1,
  UNSUPPORTED = 2 

class VoiceNameType(enum.Enum):
  jingjing = 0
  jiaojiao = 1


class ApiTts(ApiBase):
  def __init__(self, app_id, secret_key):
    ApiBase.__init__(self, app_id, secret_key)
    #TODO: customize port
    self.__client = HttpTransport()
    self.__target = "http://api.soundai.cn/tts"
    self.__max_text_size = 32 * 1024


  def tts(self, text, voice_name_type):
    if not text or not self._app_id or not self._secret_key or len(text) > self.__max_text_size:
      return "", AudioType.UNSUPPORTED

    tts_parameters = self._parameters(
        ("app_id", self._app_id),
        ("timestamp", self._timestamp()),
        ("voice_name", voice_name_type.name)
    )
    tts_address = self.__target + self._postfix("tts", tts_parameters, text)
    tts_header = {"Content-Type" : "text/plain"}
    res = self.__client.send("POST", tts_address, data=text, headers=tts_header)
    content_type = res.headers['Content-Type']

    if "mpeg" in content_type:
      return res.content, AudioType.MPEG
    else:
      return "", AudioType.UNSUPPORTED


  def tts_async(self, text, callback, voice_name_type):
    if not text or not self._app_id or not self._secret_key:
      return ErrorCode.CLOUD_ERROR_SUCCESS
        
    tts_parameters = self._parameters(
        ("app_id", self._app_id),
        ("timestamp", self._timestamp()),
        ("voice_name", voice_name_type.name)
    )
    tts_address = self.__target + self._postfix("tts", tts_parameters, text)
    tts_header = {"Content-Type" : "text/plain"}
    self.__set_on_message(callback)
    self.__client.async_send("POST", tts_address, data=text, headers=tts_header, stream=True)
    return ErrorCode.CLOUD_ERROR_SUCCESS


  def destroy(self):
    self.__client.async_join()


  def __set_on_message(self, cb):
    def wrap(response, *args, **kwargs):
      if response is None:
        cb(ErrorCode.CLOUD.ERROR_UNKNOWN_ERROR, None, None)
      
      enum_error = self._http_error_to_api_error(response.status_code)
      if response.headers['Transfer-Encoding'] == 'chunked':
        for i in response.iter_content(chunk_size=1024):
          cb(enum_error, i, response.headers['Content-Type'])
      else:
        cb(enum_error, response.content, response.headers['Content-Type'])

    self.__client.set_on_message(wrap)
    




