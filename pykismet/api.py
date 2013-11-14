"""
API Client for Akismet

"""
import urllib3
from pytool.lang import hashed_singleton


__version__ = '0.0.0-dev'
exec("c=__import__('compiler');a='__version__';l=[];g=lambda:[n.expr.value for"
        " n in l for o in n.nodes if o.name==a].pop();c.walk(c.parseFile('%s/_"
        "_init__.py'),type('v',(object,),{'visitAssign':lambda s,n:l.append(n)"
        "})());exec(a+'=g()');"%'pykismet')


class AkismetAPIError(Exception):
    """ Raised when there's an error with the Akismet API. """


@hashed_singleton
class Akismet(object):
    """
    Akismet API client.

    :param api_key: Your Akismet or Wordpress API key
    :param blog: Default value for "blog" (optional)
    :param agent: Your Application User-Agent (optional)
    :type api_key: str
    :type blog: str
    :type agent: str

    If you don't provide a value for `blog` when initializing the API instance,
    you must pass it in with each API call.

    If you don't provide a value for your application User-Agent string, the
    default value is ``pykismet/[version]``.

    Example usage:

        from pykismet import Akismet

        api = Akismet('your_api_key')

    """
    # Akismet API settings. These can be overridden in a subclass
    akismet_schema = 'http'
    """ Schema for Akismet API. """
    akismet_host = 'rest.akismet.com'
    """ Hostname for Akismet API. """
    akismet_port = 80
    """ Port number for Akismet API. """
    akismet_path = '1.1'
    """ Base path with leading and trailing slashes for Akismet API. """
    akismet_method = 'POST'
    """ HTTP method used with Akismet API. """

    # Connection settings
    pool_size = 1
    """ The connection pool size. This can be overridden in subclasses. """
    timeout = urllib3.util.Timeout(total=30.0)
    """ The request timeout setting. This can be overridden in subclasses. """
    retry = 1
    """ Number of retries before giving up. """

    # User-Agent settings
    client_agent = 'pykismet/' +  __version__
    """ The agent for this Python client. """
    app_agent = client_agent  # Just default to the same agent
    """ The agent for your application. """

    _required_params = ('user_ip', 'user_agent')  # Also blog

    def __init__(self, api_key, blog=None, agent=None):
        self.api_key = api_key
        self.blog = blog
        self.app_agent = agent or self.app_agent

        if self.akismet_schema == 'http':
            cls = urllib3.HTTPConnectionPool
        elif self.akismet_schema == 'https':
            cls = urllib3.HTTPSConnectionPool
        else:
            raise ValueError("schema is not 'http' or 'https'")

        self._http = cls(self._host(), self.akismet_port,
                maxsize=self.pool_size, timeout=self.timeout)

    def verify_key(self, blog=None):
        """
        Return ``True`` if the API key is valid for `blog` and ``False`` if
        not.

        :param str blog: URL of your blog

        """
        result = self._request('verify-key', {'blog': blog, 'key':
            self.api_key}, raise_invalid=False)

        if result == 'valid':
            return True

        return False

    def check_comment(self, **params):
        """
        Return ``True`` if the data passes the API check, and ``False`` if not.

        The `blog` parameter is optional if it was specified with this instance
        already.

        :param str blog: Blog URI
        :param str user_ip: User's IP Address
        :param str user_agent: Browser User-Agent header
        :param str referrer: HTTP referrer header (optional)
        :param str permalink: Blog post/comment permalink (optional)
        :param str comment_type: Free form type of comment (optional)
        :param str comment_author: User's name (optional)
        :param str comment_author_email: User's email address (optional)
        :param str comment_author_url: User's submitted URL (optional)
        :param str comment_content: Comment content (optional)

        """
        self._check_params(params)
        result = self._request('comment-check', params)
        if result == 'true':
            return True
        if result == 'false':
            return False

        raise AkismetAPIError("Bad API response: %r" % result)

    def submit_spam(self, **params):
        """
        Submits a spam entry to the Akismet API.

        The `blog` parameter is optional if it was specified with this instance
        already.

        :param str blog: Blog URI
        :param str user_ip: User's IP Address
        :param str user_agent: Browser User-Agent header
        :param str referrer: HTTP referrer header (optional)
        :param str permalink: Blog post/comment permalink (optional)
        :param str comment_type: Free form type of comment (optional)
        :param str comment_author: User's name (optional)
        :param str comment_author_email: User's email address (optional)
        :param str comment_author_url: User's submitted URL (optional)
        :param str comment_content: Comment content (optional)

        """
        self._check_params(params)
        self._request('submit-spam', params)

    def submit_ham(self, **params):
        """
        Submits a ham (non-spam) entry to the Akismet API.

        The `blog` parameter is optional if it was specified with this instance
        already.

        :param str blog: Blog URI
        :param str user_ip: User's IP Address
        :param str user_agent: Browser User-Agent header
        :param str referrer: HTTP referrer header (optional)
        :param str permalink: Blog post/comment permalink (optional)
        :param str comment_type: Free form type of comment (optional)
        :param str comment_author: User's name (optional)
        :param str comment_author_email: User's email address (optional)
        :param str comment_author_url: User's submitted URL (optional)
        :param str comment_content: Comment content (optional)

        """
        self._check_params(params)
        self._request('submit-ham', params)

    def _check_params(self, params):
        """
        Raise a TypeError if the required API parameters are not all present in
        the `params` dict.

        :param params: Dictionary of query parameters

        """
        for name in self._required_params:
            if not params.get(name, None):
                raise TypeError("Missing required argument: %r" % name)

    def _request(self, call, params, raise_invalid=True):
        """
        Return the HTTP body of the result of the request to the API `call`
        with query `params`.

        If `raise_invalid` is ``True`` then an exception will be raised if the
        HTTP response body is the string ``invalid``.

        :param str call: API call
        :param dict params: Query parameters to pass into the API call
        :param bool raise_invalid: Whether to raise an exception on ``invalid``

        """
        url = self._url(call)
        # Insert the default blog URL if one isn't specified
        if not params.get('blog', None):
            if not self.blog:
                raise TypeError("Missing required argument 'blog'")

            params['blog'] = self.blog

        response = self._http.request(self.akismet_method, url, params)
        data = response.data

        # Try to give a sensible error if something bad happened
        if response.status != 200:
            raise AkismetAPIError("%r status: %s" % (response.status, data))

        # Raise an exception if the API says our request was invalid
        if data == 'invalid' and raise_invalid:
            debug = response.headers.get('x-akismet-debug-help', '???')
            raise AkismetAPIError("Invalid request: %s" % debug)

        return data

    def _url(self, call):
        """
        Return a fully composed Akismet API URL.

        :param call: The API call name

        """
        url = "{schema}://{host}:{port}/{path}/{call}"
        return url.format(schema=self.akismet_schema, host=self._host(),
                port=self.akismet_port, path=self.akismet_path, call=call)

    def _host(self):
        """
        Return the API hostname composed of the API key and Akismet host.

        """
        return "{api_key}.{host}".format(api_key=self.api_key,
                host=self.akismet_host)

