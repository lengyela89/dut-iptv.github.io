from resources.lib.base.l1.constants import ADDON
from resources.lib.base.l2.log import log

try:
    unicode
except NameError:
    unicode = str

def format_string(string, _bold=False, _label=False, _color=None, _strip=False, **kwargs):
    if kwargs:
        string = string.format(**kwargs)

    if _strip:
        string = string.strip()

    if _label:
        _bold = True
        string = u'~ {} ~'.format(string)

    if _bold:
        string = u'[B]{}[/B]'.format(string)

    if _color:
        string = u'[COLOR {}]{}[/COLOR]'.format(_color, string)

    return string

def addon_string(id):
    string = ADDON.getLocalizedString(id)

    if not string:
        log("LANGUAGE: Addon didn't return a string for id: {}".format(id))
        string = unicode(id)

    return string

class BaseLanguage(object):
    ASK_USERNAME = 30001
    ASK_PASSWORD = 30002
    SET_KODI = 30005
    LIVE_TV = 30007
    SERIES = 30010
    MOVIES = 30011
    NEXT_PAGE = 30021
    CHANNELS = 30024
    HBO_SERIES = 30025
    HBO_MOVIES = 30026
    KIDS_SERIES = 30027
    SHOWMOVIESSERIES = 30028
    KIDS_MOVIES = 30029
    SEASON = 30031
    MINIMAL_CHANNELS = 30032
    LOGIN_ERROR_TITLE = 30033
    LOGIN_ERROR = 30034
    EMPTY_USER = 30035
    EMPTY_PASS = 30036

    PLUGIN_NO_DEFAULT_ROUTE = 32001
    PLUGIN_RESET_YES_NO = 32002
    PLUGIN_RESET_OK = 32003
    ROUTER_NO_FUNCTION = 32006
    ROUTER_NO_URL = 32007
    IA_NOT_FOUND = 32008
    IA_UWP_ERROR = 32009
    IA_KODI18_REQUIRED = 32010
    IA_AARCH64_ERROR = 32011
    IA_NOT_SUPPORTED = 32012
    IA_DOWNLOADING_FILE = 32014
    IA_WIDEVINE_DRM = 32015
    RESET = 32019
    PLUGIN_ERROR = 32020
    INSTALL_WV_DRM = 32021
    IA_WV_INSTALL_OK = 32022
    LOGIN = 32024
    LOGOUT = 32025
    SETTINGS = 32026
    LOGOUT_YES_NO = 32027
    SEARCH = 32029
    SEARCH_FOR = 32030
    PLUGIN_EXCEPTION = 32032
    ERROR_DOWNLOADING_FILE = 32033
    NEW_IA_VERSION = 32038
    MD5_MISMATCH = 32040
    NO_ITEMS = 32041
    NO_ERROR_MSG = 32052
    CHECKED_ENTITLEMENTS = 32053
    NO_MOVIES_SERIES = 32060
    YES_MOVIES_SERIES = 32061
    PROGSAZ = 32064
    PROGSAZDESC = 32065
    OTHERTITLES = 32066
    TITLESWITH = 32067
    OTHERTITLESDESC = 32068
    TITLESWITHDESC = 32069
    CHECK_ENTITLEMENTS = 32070
    DONE_NOREBOOT = 32071
    SEARCHMENU = 32074
    NEWSEARCH = 32075
    NEWSEARCHDESC = 32076
    TODAY = 32079
    YESTERDAY = 32080
    RESET_SESSION = 32082
    ADD_TO_WATCHLIST = 32083
    REMOVE_FROM_WATCHLIST = 32084
    WATCHLIST = 32085
    ADDED_TO_WATCHLIST = 32086
    ADD_TO_WATCHLIST_FAILED = 32087
    REMOVED_FROM_WATCHLIST = 32088
    REMOVE_FROM_WATCHLIST_FAILED = 32089
    START_FROM_BEGINNING = 32093
    TOO_MANY_DEVICES = 32094
    WATCHAHEAD = 32095
    RECOMMENDED = 32096
    SERIESBINGE = 32097
    MOSTVIEWED = 32098
    LOGIN_ERROR2 = 32100
    CHANNEL_PICKER = 320104
    START_BEGINNING = 320114
    LOGIN_SUCCESS = 320115
    PROXY_NOT_SET = 320116
    ASK_USERNAME2 = 320117
    ASK_PASSWORD2 = 320118
    EMPTY_USER2 = 320119
    EMPTY_PASS2 = 320120
    VIDEOSHOP = 320121
    DISABLE_EROTICA = 320122
    YES = 320123
    NO = 320124
    DISABLE_REGIONAL = 320125
    HOME_CONNECTION = 320126
    EXPLAIN_NO_REPLAY = 320127
    EXPLAIN_HOME_CONNECTION = 320128
    DISABLE_REGIONAL2 = 320129
    DISABLE_HOME_CONNECTION = 320130
    DISABLE_MINIMAL = 320131

    SELECT_ORDER = 330001
    DISABLED = 330002
    SELECT_ADDON = 330003
    SETUP_IPTV_FINISH_DESC = 330004
    SKIP_IPTV_FINISH_DESC = 330005
    SETUP_IPTV_FINISH = 330006
    SKIP_IPTV_FINISH = 330007
    SETUP_IPTV = 330008
    NEXT = 330009
    NEXT_SETUP_IPTV = 330010
    NEXT_SETUP_RADIO = 330011
    SELECT_RADIO = 330012
    NEXT_SETUP_ORDER = 330013
    SELECT_REPLAY = 330014
    NEXT_SETUP_REPLAY = 330015
    SELECT_LIVE = 330016
    ADD_RADIO = 330017
    DONE = 330018
    SELECT_SECONDARY = 330019
    SELECT_SECONDARY_DESC = 330020
    SKIP = 330021
    SELECT_PRIMARY = 330022
    SELECT_PRIMARY_DESC = 330023
    SKIP_DESC = 330024
    RESET_SETTINGS = 330025
    NO_ADDONS_ENABLED = 330026
    ADDON_NOT_INSTALLED_DESC = 330027
    NO_ADDONS_ENABLED_DESC = 330028
    RESET_SETTINGS_DESC = 330029
    ADDON_NOT_LOGGEDIN_DESC = 330030
    ADDON_ENABLED_DESC = 330031
    ADDONS_CONTINUE_DESC = 330032
    ADD_RADIO_DESC = 330033

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if not isinstance(attr, int):
            return attr

        return addon_string(attr)

    def __call__(self, string, **kwargs):
        if isinstance(string, int):
            string = addon_string(string)

        return format_string(string, **kwargs)

_ = BaseLanguage()