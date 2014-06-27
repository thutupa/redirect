
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from constants import Constants
import jinja2
import webapp2
import xsrfutil

class XsrfSecret(ndb.Model):
    """The app secret is stored."""
    xsrfSecret = ndb.BlobProperty(indexed=False)


# We might need to refactor it, but since it is strictly virtual, it should
# not matter.
def getAppRootKey():
    return ndb.Key('App', 1)


def insertOrUpdateSecret(secret):
    xsrf = XsrfSecret.query(ancestor=getAppRootKey()).get()
    if not xsrf:
        xsrf = XsrfSecret(parent=getAppRootKey())
    xsrf.xsrfSecret = secret
    xsrf.put()

def GetXsrfSecret():
    return XsrfSecret.query(ancestor=getAppRootKey()).get().xsrfSecret

class InsertXSRF(webapp2.RequestHandler):
    def get(self):
        secret = self.request.get(Constants.XSRF_SECRET_PARAM, '')
        assert secret
        #assert users.get_current_user() and users.is_current_user_admin()
        # decode
        secret = str(xsrfutil.base64Decode(str(secret)))
        insertOrUpdateSecret(secret)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Updated: ' + xsrfutil.base64Encode(str(GetXsrfSecret())))

