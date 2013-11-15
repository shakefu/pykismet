PyKismet - Akismet API client
=============================

PyKismet is a simple, thread safe, Python client for the Akismet API, based on
urllib3.


Example usage::

   from pykismet.api import Akismet

   api = Akismet('yourapikey', 'http://myblog.com')
   api.check_comment(user_ip='192.168.2.1', user_agent='Mozilla',
      comment_content="Hello there Akismet!")


