import json

from .base import ApiBase, ErrorCode, time
from .transport import HttpTransport


class ApiNlp(ApiBase):
  def __init__(self, app_id, secret_key):
    ApiBase.__init__(self, app_id, secret_key)
    #TODO: customize port
    self.__client = HttpTransport()
    self.__target = "http://api.soundai.cn/nlp"
    self.__ip = None
    self.__on_message=None

  def create(self):
    pass

  def nlp(self, query):
    if not query or not self._app_id or not self._secret_key:
      return ""

    nlp_parameters = self._parameters(
      ("app_id", self._app_id),
      ("timestamp", self._timestamp()),
    ) 
    nlp_json= self.__make_nlp_json(query)
    nlp_header = {"Content-Type" : "application/json"}
    nlp_address = self.__target + self._postfix("nlp", nlp_parameters, nlp_json)
    return self.__client.send("POST", nlp_address, data=nlp_json, headers=nlp_header)

  def nlp_async(self, query, callback):
    if not query or not self._app_id or not self._secret_key:
      return ErrorCode.CLOUD_ERROR_SUCCESS
        
    nlp_parameters = self._parameters(
      ("app_id", self._app_id),
      ("timestamp", self._timestamp()),
    ) 
    nlp_json= self.__make_nlp_json(query)
    nlp_header = {"Content-Type" : "application/json"}
    nlp_address = self.__target + self._postfix("nlp", nlp_parameters, nlp_json)
    self.__set_on_message(callback)
    self.__client.async_send("POST", nlp_address, data=nlp_json, headers=nlp_header)
    return ErrorCode.CLOUD_ERROR_SUCCESS

  def set_ip(ip):
    self.__ip = ip

  def destory(self):
    self.__client.async_join()

  def __set_on_message(self, cb):
    def wrap(response, *args, **kwargs):
      if response is None:
        cb(ErrorCode.CLOUD_ERROR_UNKNOWN_ERROR, None)

      enum_error = self._http_error_to_api_error(response.status_code)
      cb(enum_error, response.content)

    self.__client.set_on_message(wrap)

  def __make_nlp_json(self, query):
    j_dict = { 
        "query" : query,
        "dialogId" : "nlp_dialogId_" + str(int(time.time()*1000)),
        "deviceId" : self._app_id
    }
    if self.__ip is not None:
      j_dict["ip"] = self.__ip
      
    return json.dumps(j_dict)
    




