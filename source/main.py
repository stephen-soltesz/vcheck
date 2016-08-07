# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import webapp2
import logging

from oauth2client.appengine import oauth2decorator_from_clientsecrets
from googleapiclient.discovery import build
from googleapiclient import errors
from google.appengine.api import memcache


CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
SCOPES = [
    'email',
    'https://www.googleapis.com/auth/bigquery'
]
decorator = oauth2decorator_from_clientsecrets(
    filename=CLIENT_SECRETS,
    scope=SCOPES,
    cache=memcache)


class MainPage(webapp2.RequestHandler):

    @decorator.oauth_required
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Vello %s!' % self._get_given_name())

    def _get_given_name(self):
        """Send a request to the UserInfo API to retrieve the user's given name.

        Returns:
          User given name as a string.
        """
        decorated_http = decorator.http()
        user_info_service = build(
            serviceName='oauth2', version='v2',
            http=decorated_http)
        user_info = None
        try:
            user_info = (
                user_info_service.userinfo().get().execute(decorated_http))
        except errors.HttpError, e:
            logging.error('An error occurred: %s', e)
        if user_info and user_info.get('given_name'):
            return user_info.get('given_name')
        else:
            raise Exception('No given name found!')

    #def get(self):
    #    self.response.headers['Content-Type'] = 'text/plain'
    #    self.response.write('Zello, Vorld!')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    (decorator.callback_path, decorator.callback_handler())],
    debug=True)

#app = webapp2.WSGIApplication(
#    [('/', MainPage),],
#    debug=True)
