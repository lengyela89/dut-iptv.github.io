import collections, json, os, string, sys, xbmc, xbmcaddon

from resources.lib.api import api_get_channels, api_get_all_epg
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, CONST_ADDONS
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_addon, check_key, check_loggedin, load_channels, load_file, load_profile, load_prefs, load_order, load_radio_prefs, load_radio_order, save_profile, save_prefs, save_order, save_radio_order, save_radio_prefs, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l7 import plugin
from resources.lib.util import create_epg, create_playlist

try:
    unicode
except NameError:
    unicode = str

@plugin.route('')
def home(**kwargs):
    api_get_channels()

    folder = plugin.Folder(title='Installed Addons')

    installed = False
    loggedin = False

    addons = []

    desc = _.ADDON_NOT_INSTALLED_DESC
    desc2 = _.NO_ADDONS_ENABLED_DESC
    desc3 = _.RESET_SETTINGS_DESC
    desc4 = _.ADDON_NOT_LOGGEDIN_DESC
    desc5 = _.ADDON_ENABLED_DESC
    desc6 = _.ADDONS_CONTINUE_DESC

    for entry in CONST_ADDONS:
        if check_addon(addon=entry['addonid']):
            if check_loggedin(addon=entry['addonid']):
                color = 'green'
                loggedin = True
                addons.append(entry)
                folder.add_item(label=_(entry['label'], _bold=True, _color=color), info = {'plot': desc5}, path=plugin.url_for(func_or_url=home))
            else:
                color = 'orange'
                folder.add_item(label=_(entry['label'], _bold=True, _color=color), info = {'plot': desc4}, path=plugin.url_for(func_or_url=home))

            installed = True
        else:
            color = 'red'
            folder.add_item(label=_(entry['label'], _bold=True, _color=color), info = {'plot': desc}, path=plugin.url_for(func_or_url=home))

    if installed == True and loggedin == True:
        folder.add_item(label=_.NEXT, info = {'plot': desc6}, path=plugin.url_for(func_or_url=primary, addons=json.dumps(addons)))
    else:
        folder.add_item(label=_.NO_ADDONS_ENABLED, info = {'plot': desc2}, path=plugin.url_for(func_or_url=home))

    folder.add_item(label=_.RESET_SETTINGS, info = {'plot': desc3}, path=plugin.url_for(func_or_url=reset_settings))

    return folder

#Main menu items
@plugin.route()
def reset_settings(**kwargs):
    files = ['profile.json', 'prefs.json', 'order.json', 'radio_prefs.json', 'radio_order.json']

    for file in files:
        try:
            os.remove(ADDON_PROFILE + file)
        except:
            pass

@plugin.route()
def primary(addons, **kwargs):
    folder = plugin.Folder(title=_.SELECT_PRIMARY)

    addons = json.loads(addons)

    desc = _.SELECT_PRIMARY_DESC
    desc2 = _.SKIP_DESC

    for entry in addons:
        folder.add_item(label=_(entry['label'], _bold=True), info = {'plot': desc}, path=plugin.url_for(func_or_url=alternative, num=1, addon=entry['addonid'], addons=json.dumps(addons)))

    profile_settings = load_profile(profile_id=1)

    try:
        if len(profile_settings['addon1']) > 0:
            folder.add_item(label=_(_.SKIP, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=radio_select, num=6))
    except:
        pass

    return folder

@plugin.route()
def alternative(num, addon, addons, **kwargs):
    num = int(num)
    profile_settings = load_profile(profile_id=1)
    profile_settings['addon' + unicode(num)] = addon
    save_profile(profile_id=1, profile=profile_settings)

    folder = plugin.Folder(title=_.SELECT_SECONDARY)

    addons = json.loads(addons)
    addons2 = []

    desc = _.SELECT_SECONDARY_DESC

    for entry in addons:
        if not entry['addonid'] == addon:
            addons2.append(entry)

    for entry in addons2:
        folder.add_item(label=_(entry['label'], _bold=True), info = {'plot': desc}, path=plugin.url_for(func_or_url=alternative, num=num+1, addon=entry['addonid'], addons=json.dumps(addons2)))

    folder.add_item(label=_.DONE, info = {'plot': desc}, path=plugin.url_for(func_or_url=radio_select, num=num+1))

    return folder

@plugin.route()
def radio_select(num, **kwargs):
    num = int(num)

    profile_settings = load_profile(profile_id=1)

    for x in range(num, 6):
        profile_settings['addon' + unicode(x)] = ''

    save_profile(profile_id=1, profile=profile_settings)

    folder = plugin.Folder(title=_.ADD_RADIO)

    desc = _.ADD_RADIO_DESC

    folder.add_item(label=_.YES, info = {'plot': desc}, path=plugin.url_for(func_or_url=channel_picker_menu, type_tv_radio='live', save_all=1, radio=1))
    folder.add_item(label=_.NO, info = {'plot': desc}, path=plugin.url_for(func_or_url=channel_picker_menu, type_tv_radio='live', save_all=1, radio=0))

    return folder

@plugin.route()
def channel_picker_menu(type_tv_radio, save_all=0, radio=None, **kwargs):
    type_tv_radio = unicode(type_tv_radio)
    save_all = int(save_all)

    if not radio == None:
        radio = int(radio)
        profile_settings = load_profile(profile_id=1)
        profile_settings['radio'] = radio
        save_profile(profile_id=1, profile=profile_settings)

    if save_all == 1:
        save_all_prefs(type_tv_radio)

    if type_tv_radio == 'live':
        folder = plugin.Folder(title=_.SELECT_LIVE)
        desc2 = _.NEXT_SETUP_REPLAY
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=channel_picker_menu, type_tv_radio='replay', save_all=1))
        prefs = load_prefs(profile_id=1)
    elif type_tv_radio == 'replay':
        folder = plugin.Folder(title=_.SELECT_REPLAY)
        desc2 = _.NEXT_SETUP_ORDER
        prefs = load_prefs(profile_id=1)
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=order_picker_menu, type_tv_radio='live'))
    else:
        folder = plugin.Folder(title=_.SELECT_RADIO)
        desc2 = _.NEXT_SETUP_ORDER
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=order_picker_menu, type_tv_radio='radio'))
        prefs = load_radio_prefs(profile_id=1)

    if prefs:
        for currow in prefs:
            row = prefs[currow]
            
            if not check_key(row, type_tv_radio):
                continue
            
            if row[type_tv_radio] == 1:
                color = 'green'

                if not type_tv_radio == 'radio':
                    addon_type = row[type_tv_radio + '_addonid'].replace('plugin.video.', '')
            else:
                color = 'red'

                if not type_tv_radio == 'radio':
                    addon_type = _.DISABLED

            if not type_tv_radio == 'radio':
                label = _(row['name'] + ": " + addon_type, _bold=True, _color=color)
            else:
                label = _(row['name'], _bold=True, _color=color)

            folder.add_item(
                label = label,
                path = plugin.url_for(func_or_url=change_channel, id=currow, type_tv_radio=type_tv_radio),
                playable = False,
            )

    if type_tv_radio == 'live':
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=channel_picker_menu, type_tv_radio='replay', save_all=1))
    elif type_tv_radio == 'replay':
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=order_picker_menu, type_tv_radio='live'))
    else:
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=order_picker_menu, type_tv_radio='radio'))

    return folder

@plugin.route()
def order_picker_menu(type_tv_radio, double=None, primary=None, **kwargs):
    type_tv_radio = unicode(type_tv_radio)

    save_all_order(type_tv_radio=type_tv_radio, double=double, primary=primary)

    folder = plugin.Folder(title=_.SELECT_ORDER)

    if type_tv_radio == 'live':
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['radio']) == 1:
            desc2 = _.NEXT_SETUP_RADIO
            path = plugin.url_for(func_or_url=channel_picker_menu, type_tv_radio='radio', save_all=1)
        else:
            desc2 = _.NEXT_SETUP_IPTV
            path = plugin.url_for(func_or_url=simple_iptv_menu)

        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=path)

        prefs = load_prefs(profile_id=1)
        order = load_order(profile_id=1)
    else:
        desc2 = _.NEXT_SETUP_IPTV

        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=simple_iptv_menu))

        prefs = load_radio_prefs(profile_id=1)
        order = load_radio_order(profile_id=1)

    if order:
        for currow in order:
            row = prefs[currow]

            if int(row[type_tv_radio]) == 0:
                continue

            label = _(row['name'] + ": " + unicode(order[unicode(currow)]), _bold=True)

            folder.add_item(
                label = label,
                path = plugin.url_for(func_or_url=change_order, id=currow, type_tv_radio=type_tv_radio),
                playable = False,
            )

    if type_tv_radio == 'live':
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=path)
    else:
        folder.add_item(label=_(_.NEXT, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=simple_iptv_menu))

    return folder

@plugin.route()
def simple_iptv_menu(**kwargs):
    folder = plugin.Folder(title=_.SETUP_IPTV)

    desc = _.SETUP_IPTV_FINISH_DESC
    desc2 = _.SKIP_IPTV_FINISH_DESC
    folder.add_item(label=_(_.SETUP_IPTV_FINISH, _bold=True), info = {'plot': desc}, path=plugin.url_for(func_or_url=finish_setup, setup=1))
    folder.add_item(label=_(_.SKIP_IPTV_FINISH, _bold=True), info = {'plot': desc2}, path=plugin.url_for(func_or_url=finish_setup, setup=0))

    return folder

@plugin.route()
def finish_setup(setup=0, **kwargs):
    setup = int(setup)

    api_get_all_epg()

    create_playlist()
    create_epg()
    
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":false}}')
    xbmc.sleep(2000)
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":true}}')

    if setup == 1:
        setup_iptv()

    xbmc.executebuiltin('Dialog.Close(busydialog)')
    xbmc.executebuiltin('ActivateWindow(%d)' % 10000)

def save_all_prefs(type_tv_radio):
    if api_get_channels() == True:
        if type_tv_radio == 'radio':
            type_channels = load_channels(type='radio')
            prefs = load_radio_prefs(profile_id=1)
            found_ar = []

            for currow in type_channels:
                row = type_channels[currow]
                all_id = unicode(row['id'])
                name = unicode(row['name'])

                if not prefs or not check_key(prefs, all_id):
                    prefs[all_id] = {'radio': 1, 'name': name}

                found_ar.append(all_id)

            prefs2 = prefs.copy()

            for currow in prefs:
                if not currow in found_ar:
                    del prefs2[currow]

            save_radio_prefs(profile_id=1, prefs=prefs2)
        else:
            profile_settings = load_profile(profile_id=1)

            all_channels = load_channels(type='all')
            prefs = load_prefs(profile_id=1)
            found_ar = []

            for x in range(1, 6):
                if len(profile_settings['addon' + unicode(x)]) > 0:
                    video_addon = profile_settings['addon' + unicode(x)]

                    type_channels = load_channels(type=video_addon.replace('plugin.video.', ''))

                    VIDEO_ADDON_PROFILE = ADDON_PROFILE.replace(ADDON_ID, video_addon)
                    addon_prefs = load_file(VIDEO_ADDON_PROFILE + 'prefs.json', ext=True, isJSON=True)
                    addon_profile = load_file(VIDEO_ADDON_PROFILE + 'profile.json', ext=True, isJSON=True)

                    ziggov3 = 0

                    try:
                        if int(addon_profile['v3']) == 1:
                            ziggov3 = 1
                    except:
                        pass

                    for currow in type_channels:
                        row = type_channels[currow]

                        all_id = None

                        for currow2 in all_channels:
                            row2 = all_channels[currow2]

                            if (ziggov3 == 0 and unicode(row2[video_addon + '_id']) == unicode(row['id'])) or (ziggov3 == 1 and check_key(row2, video_addon + '_idv3') and unicode(row2[video_addon + '_idv3']) == unicode(row['id'])):
                                all_id = unicode(currow2)

                        if not all_id:
                            continue

                        if type_tv_radio == 'replay' and not check_key(prefs, all_id):
                            continue

                        disabled = False

                        if addon_prefs:
                            try:
                                if int(addon_prefs[unicode(row['id'])][type_tv_radio]) == 0:
                                    disabled = True
                            except:
                                pass

                        if disabled == True:
                            if type_tv_radio == 'live':
                                if all_id and check_key(prefs, all_id) and prefs[all_id]['live_addonid'] == video_addon:
                                    del prefs[all_id]
                            else:
                                try:
                                    if all_id and check_key(prefs, all_id) and prefs[all_id]['replay_addonid'] == video_addon:
                                        del prefs[all_id]['replay']
                                        del prefs[all_id]['replay_addonid']
                                        del prefs[all_id]['replay_auto']
                                        del prefs[all_id]['replay_channelid']
                                        del prefs[all_id]['replay_channelassetid']
                                except:
                                    pass

                            continue

                        if type_tv_radio == 'live':
                            if not prefs or not check_key(prefs, all_id):
                                prefs[all_id] = {'live': 1, 'live_addonid': video_addon, 'live_auto': 1, 'name': row['name'], 'live_channelid': row['id'], 'live_channelassetid': row['assetid'], 'channelname': row['name'], 'channelicon': row['icon']}
                            elif int(prefs[all_id]['live_auto']) == 1 and all_id and not all_id in found_ar:
                                prefs[all_id]['live'] = 1
                                prefs[all_id]['live_addonid'] = video_addon
                                prefs[all_id]['live_auto'] = 1
                                prefs[all_id]['live_channelid'] = row['id']
                                prefs[all_id]['live_channelassetid'] = row['assetid']
                        else:
                            try:
                                if (not prefs or not check_key(prefs, all_id)) or (int(prefs[all_id]['replay_auto']) == 1 and all_id and not all_id in found_ar):
                                    prefs[all_id]['replay'] = 1
                                    prefs[all_id]['replay_addonid'] = video_addon
                                    prefs[all_id]['replay_auto'] = 1
                                    prefs[all_id]['replay_channelid'] = row['id']
                                    prefs[all_id]['replay_channelassetid'] = row['assetid']
                            except:
                                prefs[all_id]['replay'] = 1
                                prefs[all_id]['replay_addonid'] = video_addon
                                prefs[all_id]['replay_auto'] = 1
                                prefs[all_id]['replay_channelid'] = row['id']
                                prefs[all_id]['replay_channelassetid'] = row['assetid']

                        found_ar.append(all_id)

            prefs2 = prefs.copy()

            if type_tv_radio == 'live':
                for currow in prefs:
                    if not currow in found_ar:
                        del prefs2[currow]

            save_prefs(profile_id=1, prefs=prefs2)

def save_all_order(type_tv_radio, double=None, primary=None):
    if type_tv_radio == 'live':
        prefs = load_prefs(profile_id=1)
        order = load_order(profile_id=1)
    else:
        prefs = load_radio_prefs(profile_id=1)
        order = load_radio_order(profile_id=1)

    found_ar = []
    last_id = None

    for currow in prefs:
        row = prefs[currow]

        if int(row[type_tv_radio]) == 0:
            continue

        found_ar.append(currow)

        if not check_key(order, unicode(currow)):
            if not last_id:
                order[unicode(currow)] = 1
            else:
                order[unicode(currow)] = order[last_id] + 1

        last_id = unicode(currow)

    order2 = order.copy()

    for currow in order:
        if not currow in found_ar:
            del order2[currow]

    order2 = collections.OrderedDict(sorted(order2.items(), key=lambda x: x[1]))
    order3 = order2.copy()

    last_value = 0

    for currow in order2:
        cur_value = order2[currow]

        if cur_value == last_value:
            cur_value += 1

        order3[currow] = cur_value
        last_value = cur_value

    order3 = collections.OrderedDict(sorted(order3.items(), key=lambda x: x[1]))

    if double and primary:
        tmp_primary = order3[primary]
        order3[primary] = order3[double]
        order3[double] = tmp_primary
        order3 = collections.OrderedDict(sorted(order3.items(), key=lambda x: x[1]))

    if type_tv_radio == 'live':
        save_order(profile_id=1, order=order3)
    else:
        save_radio_order(profile_id=1, order=order3)

@plugin.route()
def change_channel(id, type_tv_radio, **kwargs):
    if not id or len(unicode(id)) == 0:
        return False

    id = unicode(id)
    type_tv_radio = unicode(type_tv_radio)

    if type_tv_radio == 'radio':
        prefs = load_radio_prefs(profile_id=1)

        mod_pref = prefs[id]

        if int(mod_pref['radio']) == 0:
            mod_pref['radio'] = 1
        else:
            mod_pref['radio'] = 0

        prefs[id] = mod_pref
        save_radio_prefs(profile_id=1, prefs=prefs)

        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"GUI.ActivateWindow","params":{"window":"videos","parameters":["plugin://' + unicode(ADDON_ID) + '/?_=channel_picker_menu&type_tv_radio=radio&save_all=0"]}}')
    else:
        profile_settings = load_profile(profile_id=1)
        prefs = load_prefs(profile_id=1)
        all_channels = load_channels(type='all')
        type_tv_radio = unicode(type_tv_radio)

        select_list = []
        num = 0

        for x in range(1, 6):
            if len(profile_settings['addon' + unicode(x)]) > 0:
                video_addon = profile_settings['addon' + unicode(x)]

                type_channels = load_channels(type=video_addon.replace('plugin.video.', ''))

                VIDEO_ADDON_PROFILE = ADDON_PROFILE.replace(ADDON_ID, video_addon)
                addon_prefs = load_file(VIDEO_ADDON_PROFILE + 'prefs.json', ext=True, isJSON=True)
                addon_profile = load_file(VIDEO_ADDON_PROFILE + 'profile.json', ext=True, isJSON=True)

                ziggov3 = 0

                try:
                    if int(addon_profile['v3']) == 1:
                        ziggov3 = 1
                except:
                    pass

                row2 = all_channels[id]

                if ziggov3 == 1:
                    try:
                        type_id = unicode(row2[video_addon + '_idv3'])
                    except:
                        type_id = ''
                else:
                    type_id = unicode(row2[video_addon + '_id'])

                if len(type_id) > 0:
                    row = type_channels[type_id]

                    disabled = False

                    if addon_prefs:
                        try:
                            if check_key(addon_prefs, unicode(row['id'])) and int(addon_prefs[unicode(row['id'])][type_tv_radio]) == 0:
                                disabled = True
                        except:
                            pass

                    if disabled == False:
                        select_list.append(profile_settings['addon' + unicode(x)].replace('plugin.video.', ''))
                        num += 1

        select_list.append(_.DISABLED)

        selected = gui.select(_.SELECT_ADDON, select_list)
        mod_pref = prefs[id]

        if selected and selected >= 0:
            mod_pref[type_tv_radio + '_auto'] = 0

            if selected == num:
                mod_pref[type_tv_radio] = 0
                mod_pref[type_tv_radio + '_addonid'] = ''
                mod_pref[type_tv_radio + '_channelid'] = ''
                mod_pref[type_tv_radio + '_channelassetid'] = ''

                if type_tv_radio == 'live':
                    mod_pref['channelname'] = ''
                    mod_pref['channelicon'] = ''
            else:
                mod_pref[type_tv_radio] = 1
                mod_pref[type_tv_radio + '_addonid'] = 'plugin.video.' + select_list[selected]
                mod_pref[type_tv_radio + '_channelid'] = ''
                mod_pref[type_tv_radio + '_channelassetid'] = ''
                if type_tv_radio == 'live':
                    mod_pref['channelname'] = ''
                    mod_pref['channelicon'] = ''

                type_channels = load_channels(type=select_list[selected])
                row2 = all_channels[id]

                if ziggov3 == 1:
                    try:
                        type_id = unicode(row2[mod_pref[type_tv_radio + '_addonid'] + '_idv3'])
                    except:
                        type_id = ''
                else:
                    type_id = unicode(row2[mod_pref[type_tv_radio + '_addonid'] + '_id'])

                if len(type_id) > 0:
                    row = type_channels[type_id]

                    mod_pref[type_tv_radio + '_channelid'] = row['id']
                    mod_pref[type_tv_radio + '_channelassetid'] = row['assetid']

                    if type_tv_radio == 'live':
                        mod_pref['channelname'] = row['name']
                        mod_pref['channelicon'] = row['icon']

            prefs[id] = mod_pref
            save_prefs(profile_id=1, prefs=prefs)

        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"GUI.ActivateWindow","params":{"window":"videos","parameters":["plugin://' + unicode(ADDON_ID) + '/?_=channel_picker_menu&type_tv_radio=' + type_tv_radio + '&save_all=0"]}}')

@plugin.route()
def change_order(id, type_tv_radio, **kwargs):
    if not id or len(unicode(id)) == 0:
        return False

    if type_tv_radio == 'live':
        order = load_order(profile_id=1)
    else:
        order = load_radio_order(profile_id=1)

    id = unicode(id)
    type_tv_radio = unicode(type_tv_radio)

    selected = gui.numeric(_.SELECT_ORDER, order[id])
    double = None
    double_query = ''

    if selected and selected >= 0:
        for currow in order:
            if id == unicode(currow):
                continue

            if int(order[currow]) == int(selected):
                double = currow
                break

        order[id] = selected

    if type_tv_radio == 'live':
        save_order(profile_id=1, order=order)
    else:
        save_radio_order(profile_id=1, order=order)

    if double:
        double_query = '&double={double}&primary={primary}'.format(double=double, primary=id)

    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"GUI.ActivateWindow","params":{"window":"videos","parameters":["plugin://' + unicode(ADDON_ID) + '/?_=order_picker_menu' + double_query + '&type_tv_radio=' + type_tv_radio + '"]}}')

def setup_iptv():
    try:
        IPTV_SIMPLE_ADDON_ID = "pvr.iptvsimple"

        try:
            IPTV_SIMPLE = xbmcaddon.Addon(id=IPTV_SIMPLE_ADDON_ID)
        except:
            xbmc.executebuiltin('InstallAddon({})'.format(IPTV_SIMPLE_ADDON_ID), True)

            try:
                IPTV_SIMPLE = xbmcaddon.Addon(id=IPTV_SIMPLE_ADDON_ID)
            except:
                pass

        if IPTV_SIMPLE.getSettingBool("epgCache") != True:
            IPTV_SIMPLE.setSettingBool("epgCache", True)

        if IPTV_SIMPLE.getSettingInt("epgPathType") != 0:
            IPTV_SIMPLE.setSettingInt("epgPathType", 0)

        if IPTV_SIMPLE.getSetting("epgPath") != ADDON_PROFILE + "epg.xml":
            IPTV_SIMPLE.setSetting("epgPath", ADDON_PROFILE + "epg.xml")

        if IPTV_SIMPLE.getSetting("epgTimeShift") != "0":
            IPTV_SIMPLE.setSetting("epgTimeShift", "0")

        if IPTV_SIMPLE.getSettingBool("epgTSOverride") != False:
            IPTV_SIMPLE.setSettingBool("epgTSOverride", False)

        try:
            if IPTV_SIMPLE.getSettingBool("catchupEnabled") != True:
                IPTV_SIMPLE.setSettingBool("catchupEnabled", True)

            if IPTV_SIMPLE.getSetting("catchupQueryFormat") != "":
                IPTV_SIMPLE.setSetting("catchupQueryFormat", "")

            if IPTV_SIMPLE.getSettingInt("catchupDays") != 7:
                IPTV_SIMPLE.setSettingInt("catchupDays", 7)

            if IPTV_SIMPLE.getSettingInt("allChannelsCatchupMode") != 0:
                IPTV_SIMPLE.setSettingInt("allChannelsCatchupMode", 0)

            if IPTV_SIMPLE.getSettingBool("catchupPlayEpgAsLive") != False:
                IPTV_SIMPLE.setSettingBool("catchupPlayEpgAsLive", False)

            if IPTV_SIMPLE.getSettingInt("catchupWatchEpgBeginBufferMins") != 5:
                IPTV_SIMPLE.setSettingInt("catchupWatchEpgBeginBufferMins", 5)

            if IPTV_SIMPLE.getSettingInt("catchupWatchEpgEndBufferMins") != 15:
                IPTV_SIMPLE.setSettingInt("catchupWatchEpgEndBufferMins", 15)

            if IPTV_SIMPLE.getSettingBool("catchupOnlyOnFinishedProgrammes") != True:
                IPTV_SIMPLE.setSettingBool("catchupOnlyOnFinishedProgrammes", True)

            if IPTV_SIMPLE.getSettingBool("timeshiftEnabled") != False:
                IPTV_SIMPLE.setSettingBool("timeshiftEnabled", False)
        except:
            pass

        if IPTV_SIMPLE.getSettingBool("m3uCache") != True:
            IPTV_SIMPLE.setSettingBool("m3uCache", True)

        if IPTV_SIMPLE.getSettingInt("m3uPathType") != 0:
            IPTV_SIMPLE.setSettingInt("m3uPathType", 0)

        if IPTV_SIMPLE.getSetting("m3uPath") != ADDON_PROFILE + "playlist.m3u8":
            IPTV_SIMPLE.setSetting("m3uPath", ADDON_PROFILE + "playlist.m3u8")

        if IPTV_SIMPLE.getSettingInt("startNum") != 1:
            IPTV_SIMPLE.setSettingInt("startNum", 1)

        if IPTV_SIMPLE.getSettingBool("numberByOrder") != False:
            IPTV_SIMPLE.setSettingBool("numberByOrder", False)

        if IPTV_SIMPLE.getSettingInt("m3uRefreshMode") != 1:
            IPTV_SIMPLE.setSettingInt("m3uRefreshMode", 1)

        if IPTV_SIMPLE.getSettingInt("m3uRefreshIntervalMins") != 120:
            IPTV_SIMPLE.setSettingInt("m3uRefreshIntervalMins", 120)

        if IPTV_SIMPLE.getSettingInt("m3uRefreshHour") != 4:
            IPTV_SIMPLE.setSettingInt("m3uRefreshHour", 4)

        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"{}","enabled":false}}'.format(IPTV_SIMPLE_ADDON_ID))
        xbmc.sleep(2000)
        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"{}","enabled":true}}'.format(IPTV_SIMPLE_ADDON_ID))
    except:
        pass