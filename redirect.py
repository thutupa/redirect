import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
import xsrfstorage
from constants import Constants

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Action(ndb.Model):
    """Models a redirect command."""
    actionwords = ndb.StringProperty(repeated=True)
    redirect_link = ndb.StringProperty(indexed=False)
    user_id = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

    def getActionwordsAsString(self):
        return '[' + ', '.join(self.actionwords) + ']'

    def getRedirectLink(self, userInput=None):
        # TODO(syam): Actually use the user input to create the redirect
        return self.redirect_link

MAX_NUM_ACTION_WORDS = 10
MAX_ACTION_WORD_LENGTH = 20

class UserInput(object):
    def __init__(self, keywords):
        self._userInput = input
        # Split by space, upto MAX words (or (MAX - 1) splits)
        self._actionWords = keywords.split(' ', MAX_NUM_ACTION_WORDS - 1)
        for i, kw in enumerate(self._actionWords):
            if len(kw) > MAX_ACTION_WORD_LENGTH:
                kw = kw[:MAX_ACTION_WORD_LENGTH]

            self._actionWords[i] = kw.lower()
    

    def getActionWord(self, atIndex=0):
        if atIndex >= len(self._actionWords):
            return ""
        return self._actionWords[atIndex]

    def getAllActionWords(self): return self._actionWords

    def getOriginalInput(self):
        return self._userInput
    

def getAccountKey(userId):
    return ndb.Key('Account', userId)

# Proposed Final Algorithm
# 1. Lookup the matches with all action words
# 2. Score them by incidence
# 3. Use the match with the best score as long as it
#    crosses a threshold
# 4. If more then one match does, present choice to the user
# Current algorithm
# Lookup by all words.
# Get matching actions
def fetchMatchingActions(keywords, user):
    assert user
    if keywords:
        input = UserInput(keywords)
        matchingActionsQuery = Action.query(Action.actionwords.IN(input.getAllActionWords()),
                                            ancestor=getAccountKey(user.user_id()))
    else:
        matchingActionsQuery = Action.query(ancestor=getAccountKey(user.user_id()))

    return matchingActionsQuery.fetch()


class ListPage(webapp2.RequestHandler):
    # Post method is needed when the user submits attempts to use matching 
    def post(self): return self.get()
    def get(self):
        user = users.get_current_user()
        if not user:
            # Send the user to the login page
            self.redirect(users.create_login_url(self.request.uri))
            return

        assert user
        match = self.request.get(Constants.MATCH_PARAM, '')
        highlightKey = self.request.get(Constants.NEW_KEY_PARAM, '0')
        matchingUserActions = fetchMatchingActions(match, user)
        template_values = { 'user_nickname': user.nickname(),
                            'matching_actions': matchingUserActions,
                            'user_id': user.user_id(),
                            'match': match,
                            'Constants': Constants.instance(),
                            'highlight_key': int(highlightKey)}

        template = JINJA_ENVIRONMENT.get_template('list.html')
        self.response.write(template.render(template_values))

# TODO(syam): Deal with XSRF.
class AddPage(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            # Send the user to the login page
            self.redirect(users.create_login_url(self.request.uri))
            return

        assert user
        newKey = None
        if (self.request.get(Constants.ACTION_WORDS_PARAM) and
            self.request.get(Constants.REDIRECT_LINK_PARAM)):
           newAction = Action(parent=getAccountKey(user.user_id()))
           newAction.user_id = user.user_id()
           newAction.redirect_link = self.request.get(Constants.REDIRECT_LINK_PARAM)
           newAction.actionwords = UserInput(
               self.request.get(Constants.ACTION_WORDS_PARAM)).getAllActionWords()
           newKey = newAction.put()
           # TODO(syam): Figure out how to use newKey in displaying the list.
           return self.redirect(listPagePath(Constants.NEW_KEY_PARAM, str(newKey.id())))
                                
        # Fallback to the get.
        return self.get()

    def get(self):
        user = users.get_current_user()
        if not user:
            # Send the user to the login page
            self.redirect(users.create_login_url(self.request.uri))
            return

        assert user
        template_values = { 'user_nickname': user.nickname(),
                            'Constants': Constants.instance(),
                            'actionwords_input': self.request.get(Constants.ACTION_WORDS_PARAM),
                            'redirect_link_input': self.request.get(Constants.REDIRECT_LINK_PARAM)}

        template = JINJA_ENVIRONMENT.get_template('add.html')
        self.response.write(template.render(template_values))

class RedirectPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            # Send the user to the login page
            self.redirect(users.create_login_url(self.request.uri))
            return

        assert user
        match = self.request.get(Constants.MATCH_PARAM, '')
        matchingUserActions = fetchMatchingActions(match, user)
        firstAction = None
        for action in matchingUserActions:
            if firstAction is None:
                firstAction = action
            else:
                # If we get more than one result, redirect
                firstAction = None
                break

        if firstAction is None:
            return self.redirect(listPagePath(Constants.MATCH_PARAM, match))
        else:
            return self.redirect(str(firstAction.getRedirectLink(UserInput(match))))

def listPagePath(param, value):
    return Constants.LIST_PAGE_PATH + '?' + param + '=' + value

application = webapp2.WSGIApplication([
    (Constants.LIST_PAGE_PATH, ListPage),
    (Constants.ADD_PAGE_PATH, AddPage),
    (Constants.REDIRECT_PAGE_PATH, RedirectPage),
    (Constants.XSRF_SECRET_PAGE_PATH, xsrfstorage.InsertXSRF),
], debug=True)
