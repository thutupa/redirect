import webapp2
import v1.redirect

application = webapp2.WSGIApplication(
    v1.redirect.REDIRECT_SETUP, debug=True)
