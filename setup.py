from setuptools import setup

setup(
  name = "sai-openapi",
  version = '1.0.0',
  packages = [
    'openapi',
  ],
  install_requires=[
    "gevent",
    "requests",
    "ws4py",
  ],
  scripts = [],
  author  = 'SoundAI', 
  author_email = "abc@111.com",
  description = "SoundAI OpenAPI SDK",
  keywords = ["soundai", "sai", "ocr", "nlp", "tts"]
)
