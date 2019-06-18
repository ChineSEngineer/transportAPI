#from functools import partial
try:
  import gevent
  from gevent import monkey
  from gevent.pool import Pool
except ImportError:
  raise RuntimeError('Gevent is required')

try:
  import queue
except ImportError:
  import Queue as queue

import requests
from ws4py.client.geventclient import WebSocketClient

from .observers import ObserverHttp

#Monkey-pathch()
monkey.patch_all(thread=False, select=False)

class HttpTransport(object):
  def __init__(self, observer = None):
    #TODO: Configurable
    self.__pool = Pool(10)
    self.on_messsage = None
    self.on_error=None

  #TODO: partial function
  def send(self, method, url, **kwargs):
    try:
      res = requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as e:
      if self.on_error is not None:
        self.on_error(e)
      raise Exception("Internal Error")
    
    if res is None:
      e = Exception("Empty Response")
      if self.on_error is not None:
        self.on_error(e)
      raise(e)
    
    return res


  def async_send(self, method, url, **kwargs):
    try:
      self.__pool.spawn(requests.request, method, url, hooks=dict(response=self.on_message), **kwargs)
    except requests.exceptions.RequestsException as e:
      if self.on_error is not None:
        self.on_error(e)
      raise e

  def set_on_message(self, cb):
    self.on_message = cb

  def async_join(self):
    self.__pool.join()




class WebSocketTransport(object):
  def __init__(self):
    self.__connected = False
    self.__pool = Pool(1)
    self.__on_messsage = None
    self.__connection = None


  def set_on_message(self, func):
    def wrapper():
      while True:
        m = self.__connection.receive()
        if m is not None:
          func(m.data) 
        else:
          break
    
    self.__on_message = wrapper


  #TODO: Flag to make sure only one connection
  def connect(self, url):
    if self.__connected == True:
      raise RuntimeError("Connect twice")
    self.__connection = WebSocketClient(url)
    self.__connection.connect()
    #self.__connected = True
    if self.__on_message is not None:
      self.__pool.spawn(self.__on_message)
    self.__connected == True


  def send(self, msg, is_binary=False):
    self.__connection.send(msg, is_binary)

  
  def close(self):
    self.__pool.join(timeout=0)
    self.__connection.close()
    self.__connected = False
    

  
