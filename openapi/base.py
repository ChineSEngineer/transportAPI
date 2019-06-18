import sys
import time
import base64
import hashlib
import enum


class ErrorCode(enum.Enum):
  CLOUD_ERROR_SUCCESS = 0
  CLOUD_ERROR_UNAUTHORIZED = 1
  CLOUD_ERROR_UNSUPPORTED = 2
  CLOUD_ERROR_INVALID_CONFIG = 3
  CLOUD_ERROR_INVALID_ENCODING = 4
  CLOUD_ERROR_UNKNOWN_ERROR = 5


class ApiBase(object):

  def __init__(self, app_id, secret_key):
    self._app_id = app_id.strip()
    self._secret_key = secret_key.strip()

  def _signature(self, content):
    md5_obj = hashlib.md5(content)
    return base64.urlsafe_b64encode(md5_obj.digest()).decode()

  def _timestamp(self):
    return str(int(time.time()))

  def _parameters(self, *args):
    res = ""
    for tp in args:
      res += tp[0] + "=" + tp[1] + "&"
    return res[:-1]

  def _postfix(self, service, parameters, content = ""):
    res = "?" + parameters + "&signature=" + \
          self._signature(self._secret_key + \
                          service          + \
                          parameters       + \
                          content)
    return res

  def _http_error_to_api_error(self, code):
    error_map = {
      200 : ErrorCode.CLOUD_ERROR_SUCCESS,
      400 : ErrorCode.CLOUD_ERROR_UNSUPPORTED,
      401 : ErrorCode.CLOUD_ERROR_INVALID_CONFIG,
      403 : ErrorCode.CLOUD_ERROR_INVALID_CONFIG,
      404 : ErrorCode.CLOUD_ERROR_INVALID_CONFIG,
      413 : ErrorCode.CLOUD_ERROR_UNKNOWN_ERROR,
      429 : ErrorCode.CLOUD_ERROR_UNKNOWN_ERROR
    }
    return error_map.get(code, ErrorCode.CLOUD_ERROR_UNKNOWN_ERROR)


