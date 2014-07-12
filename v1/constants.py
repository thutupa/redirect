

CONSTANTS_INSTANCE = None
class Constants:
    LIST_PAGE_PATH = '/'
    ADD_PAGE_PATH = '/add'
    REDIRECT_PAGE_PATH = '/redir'
    XSRF_SECRET_PAGE_PATH = '/xsrfsecret'
    ECHO_PAGE_PATH = '/echo'

    ACTION_ID_PARAM = 'action_id'
    ACTION_WORDS_PARAM = 'actionwords'
    REDIRECT_LINK_PARAM = 'redirect_link'
    MATCH_PARAM = 'match'
    NEW_KEY_PARAM = 'new_key'
    XSRF_SECRET_PARAM = 'xsrf_secret'
    AJAX_REQUEST_PARAM = 'is_ajax_request'


    @staticmethod
    def instance():
        global CONSTANTS_INSTANCE
        if CONSTANTS_INSTANCE is None:
            CONSTANTS_INSTANCE = Constants()
        return CONSTANTS_INSTANCE

