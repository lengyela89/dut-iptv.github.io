import glob, hashlib, io, json, os, platform, pytz, re, requests, shutil, string, struct, time, unicodedata, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PATH, ADDON_PROFILE, CONST_DUT_EPG_SETTINGS, PROVIDER_NAME
from resources.lib.base.l1.encrypt import Credentials
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log

try:
    unicode
except NameError:
    unicode = str

def change_icon():
    addon_icon = ADDON_PATH + os.sep + "icon.png"
    settings_file = ADDON_PROFILE + os.sep + 'settings.json'

    if is_file_older_than_x_days(file=settings_file, days=14):
        r = requests.get(CONST_DUT_EPG_SETTINGS, stream=True)

        if r.status_code == 200:
            try:
                with open(settings_file, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            except:
                return
        else:
            return

    settingsJSON = load_file(file='settings.json', isJSON=True)

    if not md5sum(addon_icon) or settingsJSON['icon']['md5'] != md5sum(addon_icon):
        r = requests.get(settingsJSON['icon']['url'], stream=True)

        if r.status_code == 200:
            try:
                with open(addon_icon, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            except:
                return
        else:
            return

        try:
            try:
                from sqlite3 import dbapi2 as sqlite
            except:
                from pysqlite2 import dbapi2 as sqlite

            texture_file = 'Textures13.db'

            for file in glob.glob(xbmc.translatePath("special://database") + os.sep + "*Textures*"):
                texture_file = file

            TEXTURE_DB = os.path.join(xbmc.translatePath("special://database"), texture_file)

            db = sqlite.connect(TEXTURE_DB)
            query = "SELECT cachedurl FROM texture WHERE url LIKE '%addons%" + ADDON_ID + "%icon.png';"

            rows = db.execute(query)

            for row in rows:
                thumb = os.path.join(xbmc.translatePath("special://thumbnails"), unicode(row[0]))

                if os.path.isfile(thumb):
                    os.remove(thumb)

            query = "DELETE FROM texture WHERE url LIKE '%addons%" + ADDON_ID + "%icon.png';"

            db.execute(query)
            db.commit()
            db.close()
        except:
            pass

def check_key(object, key):
    if key in object and object[key] and len(unicode(object[key])) > 0:
        return True
    else:
        return False

def clear_cache():
    if not os.path.isdir(ADDON_PROFILE + "cache"):
        os.makedirs(ADDON_PROFILE + "cache")

    for file in glob.glob(ADDON_PROFILE + "cache" + os.sep + "*.json"):
        if is_file_older_than_x_days(file=file, days=1):
            os.remove(file)

    if not os.path.isdir(ADDON_PROFILE + "tmp"):
        os.makedirs(ADDON_PROFILE + "tmp")

    for file in glob.glob(ADDON_PROFILE + "tmp" + os.sep + "*.zip"):
        if is_file_older_than_x_days(file=file, days=1):
            os.remove(file)

def clear_old():
    if os.path.isfile(ADDON_PROFILE + 'settings.db'):
        try:
            shutil.rmtree(ADDON_PROFILE)

            directory = os.path.dirname(ADDON_PROFILE + os.sep + "tmp/empty.json")

            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            except:
                pass

            directory = os.path.dirname(ADDON_PROFILE + os.sep + "cache/empty.json")

            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            except:
                pass
        except:
            pass

def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = pytz.timezone(tz1)
    tz2 = pytz.timezone(tz2)

    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)

    return dt

def date_to_nl_dag(curdate):
    dag = {
        "Mon": "Maandag",
        "Tue": "Dinsdag",
        "Wed": "Woensdag",
        "Thu": "Donderdag",
        "Fri": "Vrijdag",
        "Sat": "Zaterdag",
        "Sun": "Zondag"
    }

    return dag.get(curdate.strftime("%a"), "")

def date_to_nl_maand(curdate):
    maand = {
        "January": "januari",
        "February": "februari",
        "March": "maart",
        "April": "april",
        "May": "mei",
        "June": "juni",
        "July": "juli",
        "August": "augustus",
        "September": "september",
        "October": "oktober",
        "November": "november",
        "December": "december"
    }

    return maand.get(curdate.strftime("%B"), "")

def disable_prefs(type, channels):
    prefs = load_prefs(profile_id=1)

    if channels:
        for currow in channels:
            row = channels[currow]

            if (type == 'minimal' and int(row['minimal']) == 0) or (type == 'erotica' and int(row['erotica']) == 1) or (type == 'regional' and int(row['regional']) == 1) or (type == 'home_only' and int(row['home_only']) == 1):
                mod_pref = {
                    'live': 0,
                    'replay': 0,
                }

                prefs[unicode(currow)] = mod_pref

    save_prefs(profile_id=1, prefs=prefs)

def find_highest_bandwidth(xml):
    bandwidth = 0

    result = re.findall(r'<[rR]epresentation(?:(?!<[rR]epresentation)(?!</[rR]epresentation>)[\S\s])+</[rR]epresentation>', xml)
    bandwidth_regex = r"bandwidth=\"([0-9]+)\""

    for match in result:
        if not 'id="video' in match and not 'id="Video' in match:
            continue

        match2 = re.search(bandwidth_regex, match)

        if match2:
            try:
                if int(match2.group(1)) > bandwidth:
                    bandwidth = int(match2.group(1))
            except:
                pass

    return bandwidth

def fixBadZipfile(zipFile):
    f = open(zipFile, 'r+b')
    data = f.read()
    pos = data.find('\x50\x4b\x05\x06') # End of central directory signature
    
    if (pos > 0):
        f.seek(pos + 22)   # size of 'ZIP end of central directory record'
        f.truncate()
        f.close()

def get_credentials():
    profile_settings = load_profile(profile_id=1)

    if not profile_settings or not check_key(profile_settings, 'username'):
        username = ''
    else:
        username = profile_settings['username']

    if not profile_settings or not check_key(profile_settings, 'pswd'):
        password = ''
    else:
        password = profile_settings['pswd']

    if len(username) < 50 and len(password) < 50:
        set_credentials(username, password)
        return {'username' : username, 'password' : password }

    return Credentials().decode_credentials(username, password)

def get_kodi_version():
    try:
        return int(xbmc.getInfoLabel("System.BuildVersion").split('.')[0])
    except:
        return 0

def get_system_arch():
    if xbmc.getCondVisibility('System.Platform.UWP') or '4n2hpmxwrvr6p' in xbmc.translatePath('special://xbmc/'):
        system = 'UWP'
    elif xbmc.getCondVisibility('System.Platform.Android'):
        system = 'Android'
    elif xbmc.getCondVisibility('System.Platform.IOS'):
        system = 'IOS'
    else:
        system = platform.system()

    if system == 'Windows':
        arch = platform.architecture()[0]
    else:
        try:
            arch = platform.machine()
        except:
            arch = ''

    #64bit kernel with 32bit userland
    if ('aarch64' in arch or 'arm64' in arch) and (struct.calcsize("P") * 8) == 32:
        arch = 'armv7'

    elif 'arm' in arch:
        if 'v6' in arch:
            arch = 'armv6'
        else:
            arch = 'armv7'

    elif arch == 'i686':
        arch = 'i386'

    return system, arch

def is_file_older_than_x_days(file, days=1):
    if not os.path.isfile(file):
        return True

    file_time = os.path.getmtime(file)
    totaltime = int(time.time()) - int(file_time)
    totalhours = float(totaltime) / float(3600)

    if totalhours > 24*days:
        return True
    else:
        return False

def is_file_older_than_x_minutes(file, minutes=1):
    if not os.path.isfile(file):
        return True

    file_time = os.path.getmtime(file)
    totaltime = int(time.time()) - int(file_time)
    totalminutes = float(totaltime) / float(60)

    if totalminutes > minutes:
        return True
    else:
        return False

def load_file(file, isJSON=False):
    if not os.path.isfile(ADDON_PROFILE + file):
        file = re.sub(r'[^a-z0-9.]+', '_', file).lower()

        if not os.path.isfile(ADDON_PROFILE + file):
            return None

    with io.open(ADDON_PROFILE + file, 'r', encoding='utf-8') as f:
        try:
            if isJSON == True:
                return json.load(f, object_pairs_hook=OrderedDict)
            else:
                return f.read()
        except:
            return None

def load_prefs(profile_id=1):
    prefs = load_file('prefs.json', isJSON=True)

    if not prefs:
        return OrderedDict()
    else:
        return prefs

def load_profile(profile_id=1):
    profile = load_file('profile.json', isJSON=True)

    if not profile:
        return OrderedDict()
    else:
        return profile

def md5sum(filepath):
    if not os.path.isfile(filepath):
        return None

    return hashlib.md5(open(filepath,'rb').read()).hexdigest()

def set_credentials(username, password):
    profile_settings = load_profile(profile_id=1)

    encoded = Credentials().encode_credentials(username, password)

    try:
        username = encoded['username'].decode('utf-8')
    except:
        username = encoded['username']

    try:
        pswd = encoded['password'].decode('utf-8')
    except:
        pswd = encoded['password']

    profile_settings['pswd'] = pswd
    profile_settings['username'] = username

    save_profile(profile_id=1, profile=profile_settings)

def update_prefs(profile_id=1, channels=None):
    prefs = load_prefs(profile_id=1)

    if prefs:
        for pref in prefs:
            if not pref in channels:
                prefs.pop(pref)

    if channels:
        for currow in channels:
            row = channels[currow]

            if not prefs or not check_key(prefs, unicode(currow)):
                if (settings.getBool(key='minimalChannels') == True and int(row['minimal']) == 0) or (settings.getBool(key='disableErotica') == True and int(row['erotica']) == 1) or (settings.getBool(key='disableRegionalChannels') == True and int(row['regional']) == 1) or (PROVIDER_NAME == 'kpn' and settings.getBool(key='homeConnection') == False and int(row['home_only']) == 1):
                    mod_pref = {
                        'live': 0,
                        'replay': 0,
                    }
                else:
                    if int(row['replay']) == 0:
                        mod_pref = {
                            'live': 1,
                            'replay': 0,
                        }
                    else:
                        mod_pref = {
                            'live': 1,
                            'replay': 1,
                        }

                prefs[unicode(currow)] = mod_pref

    save_prefs(profile_id=1, prefs=prefs)

def save_prefs(profile_id=1, prefs=None):
    write_file('prefs.json', data=prefs, isJSON=True)

def save_profile(profile_id=1, profile=None):
    write_file('profile.json', data=profile, isJSON=True)

def write_file(file, data, isJSON=False):
    directory = os.path.dirname(ADDON_PROFILE + file)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with io.open(ADDON_PROFILE + file, 'w', encoding="utf-8") as f:
        if isJSON == True:
            f.write(unicode(json.dumps(data, ensure_ascii=False)))
        else:
            f.write(unicode(data))