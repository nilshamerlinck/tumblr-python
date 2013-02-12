import json
import logging
import oauth2 as oauth
import urllib
import urlparse

class TumblrClient(object):
    """A Python client for accessing the Tumblr v2 API"""

    API_SCHEME = 'http'
    API_HOST = 'api.tumblr.com'

    USER_URLS = {
        'info': '/v2/user/info',
        'dashboard': '/v2/user/dashboard',
        'likes': '/v2/user/likes',
        'following': '/v2/user/following',
        'follow': '/v2/user/follow',
        'unfollow': '/v2/user/unfollow',
        'like': '/v2/user/like',
        'unlike': '/v2/user/unlike',
        }

    BLOG_URLS = {
        'info': '/v2/blog/%(hostname)s/info',
        'avatar': '/v2/blog/%(hostname)s/avatar',
        'avatar/size': '/v2/blog/%(hostname)s/avatar/%(size)s',
        'followers': '/v2/blog/%(hostname)s/followers',
        'posts': '/v2/blog/%(hostname)s/posts',
        'posts/type': '/v2/blog/%(hostname)s/posts/%(type)s',
        'queue': '/v2/blog/%(hostname)s/posts/queue',
        'draft': '/v2/blog/%(hostname)s/posts/draft',
        'submission': '/v2/blog/%(hostname)s/posts/submission',
        'post': '/v2/blog/%(hostname)s/post',
        'edit': '/v2/blog/%(hostname)s/post/edit',
        'reblog': '/v2/blog/%(hostname)s/post/reblog',
        'delete': '/v2/blog/%(hostname)s/post/delete',
    }

    def __init__(self, consumer, token=None):
        self.consumer = consumer
        self.token = token

    def get_api_key(self):
        return self.consumer.key

    def build_api_key_url(self, format_string, format_params={},
        query_params={}):
        """Builds a URL and adds the client's API key"""
        if 'api_key' not in query_params:
            query_params['api_key'] = self.get_api_key()
        return self.build_url(format_string, format_params, query_params)

    def build_url(self, format_string, format_params={}, query_params={}):
        path = format_string % format_params
        query_string = urllib.urlencode(query_params)

        parsed_url = urlparse.SplitResult(scheme=self.API_SCHEME,
            netloc=self.API_HOST, path=path, query=query_string,
            fragment=None)

        request_url = urlparse.urlunsplit(parsed_url)

        logging.debug('Built URL: %s ' % request_url)

        return request_url

    def make_unauthorized_request(self, request_url):
        response = urllib.urlopen(request_url)

        try:
            json_response = json.load(response)
        except ValueError, e:
            logging.error('Invalid response: %s (%d)' % (e,
                response.getcode()))
            return None

        return json_response

    def make_oauth_request(self, request_url, method='GET', body=None):
        if not self.consumer or not self.token:
            logging.error('Missing OAuth credentials')
            return None

        oauth_client = oauth.Client(self.consumer, self.token)
        if body:
            response, content = oauth_client.request(request_url, method,
                body)
        else:
            response, content = oauth_client.request(request_url, method)

        try:
            json_response = json.loads(content)
        except ValueError, e:
            logging.error('Invalid response: %s (%s)' % (e,
                response['status']))
            return None

        return json_response

    def get_user_info(self, user, private=False):
        request_url = self.build_api_key_url(self.USER_URLS['info'], { 'user': user })        

        if private:
            return self.make_oauth_request(request_url)
        else:
            return self.make_unauthorized_request(request_url)

    def get_blog_info(self, hostname, private=False):
        request_url = self.build_api_key_url(self.BLOG_URLS['info'], { 'hostname': hostname })

        if private:
            return self.make_oauth_request(request_url)
        else:
            return self.make_unauthorized_request(request_url)

    def get_blog_posts(self, hostname, private=False, post_type=None, request_params={}):
        format_params = { 'hostname': hostname }
        format_string = self.BLOG_URLS['posts']
        if post_type:
            format_params['type'] = post_type
            format_string = self.BLOG_URLS['posts/type']
        
        request_url = self.build_api_key_url(format_string,
                                             format_params=format_params,
                                             query_params=request_params)

        if private:
            return self.make_oauth_request(request_url)    
        else:
            return self.make_unauthorized_request(request_url)

    def get_blog_avatar_url(self, hostname, size=None):
        format_params = { 'hostname': hostname }
        format_string = self.BLOG_URLS['avatar']

        if size:
            format_params['size'] = size
            format_string = self.BLOG_URLS['avatar/size']

        return self.build_url(format_string, format_params)

    def get_blog_followers(self, hostname, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_api_key_url(self.BLOG_URLS['followers'],
                                             format_params=format_params,
                                             query_params=request_params)

        return self.make_oauth_request(request_url)

    def get_blog_queue(self, hostname, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_api_key_url(self.BLOG_URLS['queue'],
                                             format_params=format_params,
                                             query_params=request_params)

        return self.make_oauth_request(request_url)

    def get_blog_drafts(self, hostname, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_api_key_url(self.BLOG_URLS['draft'],
                                             format_params=format_params,
                                             query_params=request_params)

        return self.make_oauth_request(request_url)

    def get_blog_submissions(self, hostname, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_api_key_url(self.BLOG_URLS['submission'],
                                             format_params=format_params,
                                             query_params=request_params)

        return self.make_oauth_request(request_url)

    def create_post(self, hostname, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_url(self.BLOG_URLS['post'],
                                     format_params=format_params)

        return self.make_oauth_request(request_url, method='POST',
            body=urllib.urlencode(request_params))

    def edit_post(self, hostname, post_id, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_url(self.BLOG_URLS['edit'],
                                     format_params=format_params)

        if 'id' not in request_params:
            request_params['id'] = post_id

        return self.make_oauth_request(request_url, method='POST',
            body=urllib.urlencode(request_params))

    def reblog_post(self, hostname, reblog_key, request_params={}):
        format_params = { 'hostname': hostname }

        request_url = self.build_url(self.BLOG_URLS['edit'],
                                     format_params=format_params)

        if 'reblog_key' not in request_params:
            request_params['reblog_key'] = reblog_key

        return self.make_oauth_request(request_url, method='POST',
            body=urllib.urlencode(request_params))

    def delete_post(self, hostname, post_id):
        format_params = { 'hostname': hostname }

        request_url = self.build_url(self.BLOG_URLS['delete'],
                                     format_params=format_params)

        request_params = {
            'id': post_id,
        }

        return self.make_oauth_request(request_url, method='POST',
            body=urllib.urlencode(request_params))

class TumblrOAuthClient(object):
    REQUEST_TOKEN_URL = 'https://www.tumblr.com/oauth/request_token'
    AUTHORIZE_URL = 'https://www.tumblr.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'
    XAUTH_ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'

    def __init__(self, consumer_key, consumer_secret):
        self.consumer = oauth.Consumer(consumer_key, consumer_secret)

    def get_authorize_url(self):
        client = oauth.Client(self.consumer)
        resp, content = client.request(self.REQUEST_TOKEN_URL, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])

        self.request_token = dict(urlparse.parse_qsl(content))
        return "%s?oauth_token=%s" % (self.AUTHORIZE_URL,
            self.request_token['oauth_token'])

    def get_access_token(self, oauth_verifier):
        token = oauth.Token(self.request_token['oauth_token'],
            self.request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)

        resp, content = client.request(self.ACCESS_TOKEN_URL, "POST")
        access_token = dict(urlparse.parse_qsl(content))

        return oauth.Token(access_token['oauth_token'],
            access_token['oauth_token_secret'])
