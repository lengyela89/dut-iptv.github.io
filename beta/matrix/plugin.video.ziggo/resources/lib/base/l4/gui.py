import sys, traceback, xbmc, xbmcgui
from contextlib import contextmanager

from resources.lib.base.l1.constants import ADDON_ICON, ADDON_ID, ADDON_NAME
from resources.lib.base.l3.language import _

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

def _make_heading(heading=None):
    return heading if heading else ADDON_NAME

def notification(message, heading=None, icon=None, time=3000, sound=False):
    heading = _make_heading(heading)
    icon = ADDON_ICON if not icon else icon

    xbmcgui.Dialog().notification(heading, message, icon, time, sound)

def refresh():
    xbmc.executebuiltin('Container.Refresh')

def select(heading=None, options=None, autoclose=None, **kwargs):
    heading = _make_heading(heading)
    options = options or []

    if get_kodi_version() < 17:
        kwargs.pop('preselect', None)
        kwargs.pop('useDetails', None)

    if autoclose:
        kwargs['autoclose'] = autoclose

    _options = []
    for option in options:
        if issubclass(type(option), Item):
            option = option.label if get_kodi_version() < 17 else option.get_li()

        _options.append(option)

    return xbmcgui.Dialog().select(heading, _options, **kwargs)

def redirect(location):
    xbmc.executebuiltin('Container.Update({},replace)'.format(location))

def exception(heading=None):
    if not heading:
        heading = _(_.PLUGIN_EXCEPTION, addon=ADDON_NAME)

    exc_type, exc_value, exc_traceback = sys.exc_info()

    tb = []
    for trace in reversed(traceback.extract_tb(exc_traceback)):
        if ADDON_ID in trace[0]:
            trace = list(trace)
            trace[0] = trace[0].split(ADDON_ID)[1]
            tb.append(trace)

    error = '{}\n{}'.format(''.join(traceback.format_exception_only(exc_type, exc_value)), ''.join(traceback.format_list(tb)))

    text(error, heading=heading)

class Progress(object):
    def __init__(self, message, heading=None, percent=0, background=False):
        heading = _make_heading(heading)
        if background:
            self._dialog = xbmcgui.DialogProgressBG()
        else:
            self._dialog = xbmcgui.DialogProgress()

        self._dialog.create(heading, *self._get_args(message))
        self.update(percent)

    def update(self, percent=0, message=None):
        self._dialog.update(int(percent), *self._get_args(message))

    def _get_args(self, message):
        if message is not None and get_kodi_version() < 19:
            args = message.split('\n')[:3]
            while len(args) < 3:
                args.append(' ')
        else:
            args = [message]

        return args

    def iscanceled(self):
        return self._dialog.iscanceled()

    def close(self):
        self._dialog.close()

def progressbg(message='', heading=None, percent=0):
    heading = _make_heading(heading)

    dialog = xbmcgui.DialogProgressBG()
    dialog.create(heading, message)
    dialog.update(int(percent))

    return dialog

@contextmanager
def progress(message='', heading=None, percent=0):
    dialog = Progress(message, heading)
    dialog.update(percent)

    try:
        yield dialog
    finally:
        dialog.close()

def input(message, default='', hide_input=False, **kwargs):
    if hide_input:
        kwargs['option'] = xbmcgui.ALPHANUM_HIDE_INPUT

    return xbmcgui.Dialog().input(message, default, **kwargs)

def numeric(message, default='', type=0, **kwargs):
    try:
        return int(xbmcgui.Dialog().numeric(type, message, defaultt=str(default), **kwargs))
    except:
        return None

def error(message, heading=None):
    heading = heading or _(_.PLUGIN_ERROR, addon=ADDON_NAME)
    return ok(message, heading)

def ok(message, heading=None):
    heading = _make_heading(heading)
    return xbmcgui.Dialog().ok(heading, message)

def text(message, heading=None, **kwargs):
    heading = _make_heading(heading)

    return xbmcgui.Dialog().textviewer(heading, message)

def yes_no(message, heading=None, autoclose=120000, **kwargs):
    heading = _make_heading(heading)

    if autoclose:
        kwargs['autoclose'] = autoclose

    return xbmcgui.Dialog().yesno(heading, message, **kwargs)

def get_kodi_version():
    try:
        return int(xbmc.getInfoLabel("System.BuildVersion").split('.')[0])
    except:
        return 0

class Item(object):
    def __init__(self, id=None, label='', label2='', path=None, playable=False, info=None, context=None,
            headers=None, cookies=None, properties=None, is_folder=None, art=None, inputstream=None,
            video=None, audio=None, subtitles=None, specialsort=None):

        self.id = id
        self.label = label
        self.label2 = label2
        self.path = path
        self.info = dict(info or {})
        self.headers = dict(headers or {})
        self.cookies = dict(cookies or {})
        self.properties = dict(properties or {})
        self.art = dict(art or {})
        self.video = dict(video or {})
        self.audio = dict(audio or {})
        self.context = list(context or [])
        self.subtitles = list(subtitles or [])
        self.playable = playable
        self.inputstream = inputstream
        self.mimetype = None
        self._is_folder = is_folder
        self.specialsort = specialsort

    def update(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    @property
    def is_folder(self):
        return not self.playable if self._is_folder == None else self._is_folder

    @is_folder.setter
    def is_folder(self, value):
        self._is_folder = value

    def get_url_headers(self, only_user_agent=False):
        string = ''
        for key in self.headers:
            if only_user_agent == False or key == 'User-Agent':
                string += u'{0}={1}&'.format(key, quote(u'{}'.format(self.headers[key]).encode('utf8')))

        if self.cookies:
            string += 'Cookie='
            for key in self.cookies:
                string += u'{0}%3D{1}; '.format(key, quote(u'{}'.format(self.cookies[key]).encode('utf8')))

        return string.strip('&')

    def get_li(self):
        if get_kodi_version() < 18:
            li = xbmcgui.ListItem()
        else:
            li = xbmcgui.ListItem(offscreen=True)

        if self.label:
            li.setLabel(self.label)
            if not self.info.get('plot'):
                self.info['plot'] = self.label

            if not self.info.get('title'):
                self.info['title'] = self.label

        if self.label2:
            li.setLabel2(self.label2)

            if not self.info.get('tagline'):
                self.info['tagline'] = self.label2

        if self.info:
            li.setInfo('video', self.info)

        if self.specialsort:
            li.setProperty('specialsort', self.specialsort)

        if self.video:
            li.addStreamInfo('video', self.video)

        if self.audio:
            li.addStreamInfo('audio', self.audio)

        if self.art:
            if 'thumb' not in self.art:
                self.art['thumb'] = ''

            if 'poster' not in self.art:
                self.art['poster'] = self.art.get('thumb')

            if 'fanart' not in self.art:
                self.art['fanart'] = ''

            li.setArt({'thumb': self.art.get('thumb'), 'icon': self.art.get('thumb'), 'fanart': self.art.get('fanart')})

        if self.playable:
            li.setProperty('IsPlayable', 'true')

        if self.context:
            li.addContextMenuItems(self.context)

        if self.subtitles:
            li.setSubtitles(self.subtitles)

        for key in self.properties:
            li.setProperty(key, u'{}'.format(self.properties[key]))

        headers = self.get_url_headers()

        if self.inputstream and self.inputstream.check():
            if get_kodi_version() < 19:
                li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            else:
                li.setProperty('inputstream', 'inputstream.adaptive')

            li.setProperty('inputstream.adaptive.manifest_type', self.inputstream.manifest_type)

            if self.inputstream.media_renewal_url:
                li.setProperty('inputstream.adaptive.media_renewal_url', self.inputstream.media_renewal_url)

            if self.inputstream.media_renewal_time:
                li.setProperty('inputstream.adaptive.media_renewal_time', str(self.inputstream.media_renewal_time))

            if self.inputstream.license_type:
                li.setProperty('inputstream.adaptive.license_type', self.inputstream.license_type)

            streamheaders = self.get_url_headers(only_user_agent=True)

            if streamheaders:
                li.setProperty('inputstream.adaptive.stream_headers', streamheaders)

            if self.inputstream.license_key:
                li.setProperty('inputstream.adaptive.license_key', '{url}|Content-Type={content_type}&{headers}|{challenge}|{response}'.format(
                    url = self.inputstream.license_key,
                    headers = headers,
                    content_type = self.inputstream.content_type,
                    challenge = self.inputstream.challenge,
                    response = self.inputstream.response,
                ))
            elif headers:
                li.setProperty('inputstream.adaptive.license_key', '|{0}'.format(headers))

            if self.inputstream.mimetype:
                li.setMimeType(self.inputstream.mimetype)
                li.setContentLookup(False)

        if self.mimetype:
            li.setMimeType(self.mimetype)
            li.setContentLookup(False)

        if headers and '|' not in self.path:
            self.path = u'{}|{}'.format(self.path, headers)

        if self.path:
            li.setPath(self.path)

        return li

    def play(self):
        li = self.get_li()
        xbmc.Player().play(self.path, li)
