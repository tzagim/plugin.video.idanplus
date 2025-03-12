# -*- coding: utf-8 -*-
import sys, os, datetime, json
import xbmc, xbmcplugin, xbmcaddon
import resources.lib.common as common
import resources.lib.epg as epg
import resources.lib.iptv as iptv
import resources.lib.baseChannels as baseChannels

if common.py2:
	reload(sys)
	sys.setdefaultencoding('utf-8')

Addon = xbmcaddon.Addon(common.AddonID)
AddonName = Addon.getAddonInfo("name")
icon = Addon.getAddonInfo('icon')
imagesDir = common.imagesDir
profileDir = common.profileDir
favoritesFile = os.path.join(profileDir, 'favorites.json')
if not os.path.isfile(favoritesFile):
	common.WriteList(favoritesFile, [])


def GetCategoriesList():
	name = common.GetLabelColor("מועדפי עידן פלוס", bold=True, color="none")
	common.addDir(name, '', 10, icon, infos={"Title": name}, addFav=False)
	name = common.GetLabelColor("חיפוש תכניות", bold=True, color="none")
	common.addDir(name, '', 4, icon, infos={"Title": name}, addFav=False)
	name = common.GetLabelColor("טלויזיה", bold=True, color="none")
	common.addDir(name, '', 1, icon, infos={"Title": name})
	name = common.GetLabelColor("VOD", bold=True, color="none")
	common.addDir(name, '', 2, icon, infos={"Title": name})
	name = common.GetLabelColor("רדיו", bold=True, color="none")
	common.addDir(name, '', 3, icon, infos={"Title": name})
	name = common.GetLabelColor("תכניות רדיו", bold=True, color="none")
	common.addDir(name, '', 12, icon, infos={"Title": name})
	name = common.GetLabelColor("פודקאסטים", bold=True, color="none")
	common.addDir(name, '', 13, icon, infos={"Title": name})
	name = common.GetLabelColor("מוזיקה", bold=True, color="none")
	common.addDir(name, '', 14, icon, infos={"Title": name})
	name = common.GetLabelColor("הגדרות", bold=True, color="none")
	common.addDir(name, 'Addon.OpenSettings', 6, icon, infos={"Title": name}, moreData=common.AddonID, isFolder=False)

def GetUserChannels(type='tv'):
	userChannels = []
	if type == 'tv':
		channels = baseChannels.TvChannels
	elif type == 'radio':
		channels = baseChannels.RadioChannels
	for channel in channels:
		channel['index'] = common.GetIntSetting(channel['ch'], channel['index'])
	channels = sorted(channels, key=lambda k: k['index']) 
	for channel in channels:
		if channel['index'] != 0:
			userChannels.append(channel)
	userChannels = sorted(userChannels, key=lambda k: k['index'])
	return userChannels

def LiveChannels():
	if common.GetAddonSetting("tvShortcut") == 'true':
		name = common.GetLabelColor(common.GetLocaleString(30652), bold=True, color="none")
		common.addDir(name, 'ActivateWindow', 6, icon, infos={"Title": name}, moreData='tvchannels', isFolder=False)
	nowEPG = epg.GetNowEPG()
	channels = GetUserChannels(type='tv')
	for channel in channels:
		programs = [] if channel['tvgID'] == '' else nowEPG.get(channel['tvgID'], [])
		LiveChannel(common.GetLocaleString(channel['nameID']), channel['channelID'], channel['mode'], channel['image'], channel['module'], contextMenu=[], resKey=channel['resKey'], programs=programs, tvgID=channel['tvgID'], type='tv')

def LiveChannel(name, url, mode, iconimage, module, contextMenu=[], choose=True, resKey='', bitrate='', programs=[], tvgID='', addFav=True, type=None):
	displayName = common.GetLabelColor(name, keyColor="chColor", bold=True)
	description = ''
	iconimage = common.GetIconFullPath(iconimage)
	
	if resKey == '' and bitrate == '':
		bitrate = 'best'
	else:
		if bitrate == '':
			bitrate = common.GetAddonSetting(resKey)
			if bitrate == '':
				bitrate = 'best'
		if addFav:
			contextMenu.insert(0, (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode={3}&iconimage={4}&moredata=set_{5}&module={6})'.format(sys.argv[0], url, common.quote_plus(displayName), mode, common.quote_plus(iconimage), resKey, module)))
	if choose:
		contextMenu.insert(0, (common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode={3}&iconimage={4}&moredata=choose&module={5})'.format(sys.argv[0], url, common.quote_plus(displayName), mode, common.quote_plus(iconimage), module)))
	if type is not None:
		is_startup_ch = type == 'tv'
		startup_id = 'startup_ch' if is_startup_ch else 'startup_rd'
		is_startup_id = 'is_startup_ch' if type == 'tv' else 'is_startup_rd'
		if common.Addon.getSettingBool(is_startup_id) and common.Addon.getSettingString(startup_id) == name:
			string_id = 32007 if is_startup_ch else 32008
			add_remove_startup = 18
		else:
			string_id = 32001 if is_startup_ch else 32002
			add_remove_startup = 17
		contextMenu.insert(0, (common.GetLocaleString(string_id), 'RunPlugin({0}?name={1}&mode={2}&moredata={3})'.format(sys.argv[0], name, add_remove_startup, type)))
	if len(programs) > 0:
		contextMenu.insert(0, (common.GetLocaleString(30030), 'Container.Update({0}?url={1}&name={2}&mode=2&iconimage={3}&module=epg)'.format(sys.argv[0], tvgID, common.quote_plus(name), common.quote_plus(iconimage))))
		programTime = common.GetLabelColor("[{0}-{1}]".format(datetime.datetime.fromtimestamp(programs[0]["start"]).strftime('%H:%M'), datetime.datetime.fromtimestamp(programs[0]["end"]).strftime('%H:%M')), keyColor="timesColor")
		programName = common.GetLabelColor(common.encode(programs[0]["name"], 'utf-8'), keyColor="prColor", bold=True)
		displayName = GetChannelName(programName, programTime, displayName, channelNameFormat)
		description = '{0}[CR]{1}'.format(programName, common.encode(programs[0]["description"], 'utf-8'))
		if len(programs) > 1:
			nextProgramName = common.GetLabelColor(common.encode(programs[1]["name"], 'utf-8'), keyColor="prColor", bold=True)
			nextProgramTime = common.GetLabelColor("[{0}-{1}]".format(datetime.datetime.fromtimestamp(programs[1]["start"]).strftime('%H:%M'), datetime.datetime.fromtimestamp(programs[1]["end"]).strftime('%H:%M')), keyColor="timesColor")
			description = GetDescription(description, nextProgramTime, nextProgramName, channelNameFormat)
	contextMenu.insert(0, (common.GetLocaleString(32009), 'RunPlugin({0}?mode=19)'.format(sys.argv[0])))
	urlParamsData = {'name': common.GetLabelColor(name, keyColor="chColor", bold=True), 'tvgID': tvgID} if addFav else {}
	common.addDir(displayName, url, mode, iconimage, infos={"Title": displayName, "Plot": description,'mediatype': 'movie'}, contextMenu=contextMenu, moreData=bitrate, module=module, isFolder=False, isPlayable=True, addFav=addFav, urlParamsData=urlParamsData)

def GetChannelName(programName, programTime, displayName, channelNameFormat):
	if channelNameFormat == 0:
		chName = " {0} - {1} {2} ".format(displayName, programName, programTime)
	elif channelNameFormat == 1:
		chName = " {0}  {1}  {2} ".format(displayName, programTime, programName)
	elif channelNameFormat == 2:
		chName = " {0} {1} - {2} ".format(programTime, programName, displayName)
	elif channelNameFormat == 3:
		chName = "  {0}  {1}  {2} ".format(programName, programTime, displayName)
	return chName
	
def GetDescription(description, nextProgramTime, nextProgramName, channelNameFormat):
	if channelNameFormat == 0 or channelNameFormat == 1:
		description = ' {0}[CR][CR]{1} {2} '.format(description, nextProgramTime, nextProgramName)
	elif channelNameFormat == 2 or channelNameFormat == 3:
		description = ' {0}[CR][CR]{1} {2} '.format(description, nextProgramName, nextProgramTime)
	return description

def VODs():
	name = common.GetLabelColor(common.GetLocaleString(30602), bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath("kan.jpg"), infos={"Title": name}, module='kan')
	name = common.GetLabelColor(common.GetLocaleString(30603), bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath("mako.png"), infos={"Title": name}, module='keshet')
	name = common.GetLabelColor(common.GetLocaleString(30604), bold=True, color="none")
	common.addDir(name, '', -1, common.GetIconFullPath("13.jpg"), infos={"Title": name}, module='reshet')
	name = common.GetLabelColor(common.GetLocaleString(30606), bold=True, color="none")
	common.addDir(name, '', -1, common.GetIconFullPath("14tv.png"), infos={"Title": name}, module='14tv')
	name = common.GetLabelColor(common.GetLocaleString(30607), bold=True, color="none")
	common.addDir(name, 'https://www.kankids.org.il', 5, common.GetIconFullPath("23tv.jpg"), infos={"Title": name}, module='kan')
	name = common.GetLabelColor("כאן - ארכיון", bold=True, color="none")
	common.addDir(name, 'https://www.kan.org.il/lobby/archive/', 41,  common.GetIconFullPath("kan.jpg"), infos={"Title": name}, module='kan')
	name = common.GetLabelColor(common.GetLocaleString(30608), bold=True, color="none")
	common.addDir(name, 'https://www.mako.co.il/mako-vod-index?filter=provider&vcmId=3377c13070733210VgnVCM2000002a0c10acRCRD', 1, common.GetIconFullPath("24telad.png"), infos={"Title": name}, module='keshet')
	name = common.GetLabelColor(common.GetLocaleString(30630), bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath("9tv.png"), infos={"Title": name}, module='9tv')
	name = common.GetLabelColor(common.GetLocaleString(30900), bold=True, color="none")
	common.addDir(name, '', -1, common.GetIconFullPath("Sport5.png"), infos={"Title": name}, module='sport5')
	name = common.GetLabelColor(common.GetLocaleString(31000), bold=True, color="none")
	common.addDir(name, '', -1, common.GetIconFullPath("sport1.jpg"), infos={"Title": name}, module='sport1')

def Radios():
	if common.GetAddonSetting("radioShortcut") == 'true':
		name = common.GetLabelColor(common.GetLocaleString(30732), bold=True, color="none")
		common.addDir(name, 'ActivateWindow', 6, icon, infos={"Title": name}, moreData='radiochannels', isFolder=False)
	nowEPG = epg.GetNowEPG()
	channels = GetUserChannels(type='radio') 
	for channel in channels:
		programs = [] if channel['tvgID'] == '' else nowEPG.get(channel['tvgID'], [])
		LiveChannel(common.GetLocaleString(channel['nameID']), channel['channelID'], channel['mode'], channel['image'], channel['module'], contextMenu=[], choose=False, programs=programs, tvgID=channel['tvgID'], type='radio')

def RadioVODs():
	name = common.GetLabelColor("תכניות רדיו - כאן", bold=True, color="none")
	common.addDir(name, '', 21, common.GetIconFullPath('kan.jpg'), infos={"Title": name}, module='kan')
	name = common.GetLabelColor("תכניות רדיו ספורט 5", bold=True, color="none")
	common.addDir(name, '', 20, common.GetIconFullPath('Sport5.png'), infos={"Title": name}, module='sport5')
	name = common.GetLabelColor("תכניות רדיו - 89.1fm", bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath('891fm.png'), infos={"Title": name}, module='891fm')
	name = common.GetLabelColor("תכניות רדיו - 106.4fm", bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath('1064fm.jpg'), infos={"Title": name}, module='1064fm')
	
def Musics():
	name = common.GetLabelColor("מוזיקה - גלגל\"צ", bold=True, color="none")
	common.addDir(name, 'glglz', 1, common.GetIconFullPath('glglz.jpg'), infos={"Title": name}, module='glz')
	name = common.GetLabelColor("מוזיקה - eco99fm", bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath('99fm.png'), infos={"Title": name}, module='99fm')
	name = common.GetLabelColor("מוזיקה - 100fm", bold=True, color="none")
	common.addDir(name, '', 0, common.GetIconFullPath('100fm.jpg'), infos={"Title": name}, module='100fm')

def Podcasts():
	name = common.GetLabelColor("פודקאסטים - כאן", bold=True, color="none")
	common.addDir(name, '4451', 31, common.GetIconFullPath('kan.jpg'), infos={"Title": name}, module='kan')
	name = common.GetLabelColor("פודקאסטים לילדים - כאן", bold=True, color="none")
	common.addDir(name, '', 33, common.GetIconFullPath('kan.jpg'), infos={"Title": name}, module='kan')
	name = common.GetLabelColor("פודקאסטים ספורט 5", bold=True, color="none")
	common.addDir(name, '', 20, common.GetIconFullPath('Sport5.png'), infos={"Title": name}, module='sport5')

def MakeIPTVfiles():
	iptv.MakeIPTVlist(GetUserChannels(type='tv') + GetUserChannels(type='radio'))
	if common.isFileOld(common.epgFile):
		epg.GetEPG()
	iptv.MakeChannelsGuide()

def AddFavorite(url):
	favoritesList = common.ReadList(favoritesFile)
	if any(u == url for u in favoritesList):
		return
	favoritesList.append(common.decode(url, "utf-8"))
	common.WriteList(favoritesFile, favoritesList)
	xbmc.executebuiltin("Notification({0}, {1}, 5000, {2})".format(AddonName, common.GetLocaleString(30028), icon))

def RemoveFavortie(index):
	favoritesList = common.ReadList(favoritesFile)
	if index < 0 or index >= len(favoritesList):
		return
	favoritesList.remove(favoritesList[index])
	common.WriteList(favoritesFile, favoritesList)
	xbmc.executebuiltin("Notification({0}, {1}, 5000, {2})".format(AddonName, common.GetLocaleString(30029), icon))
	xbmc.executebuiltin("Container.Refresh()")

def GetModuleName(module, mode, moreData, catName=''):
	mode = str(mode)
	moduleName = ''
	if module == 'kan': 		moduleName = common.GetLocaleString(30400) if catName == '' else catName
	elif module == 'keshet': 	moduleName = common.GetLocaleString(30603)
	elif module == 'reshet': 	moduleName = common.GetLocaleString(30604)
	elif module == '14tv': 		moduleName = common.GetLocaleString(30606)
	elif module == '9tv': 		moduleName = common.GetLocaleString(30630)
	elif module == '891fm': 	moduleName = common.GetLocaleString(30734)
	elif module == 'sport5': 	moduleName = common.GetLocaleString(30632)
	elif module == 'sport1': 	moduleName = common.GetLocaleString(31000)
	elif module == '99fm': 		moduleName = common.GetLocaleString(30704)
	elif module == 'glz': 		moduleName = common.GetLocaleString(30702)
	elif module == '100fm': 	moduleName = common.GetLocaleString(30726)
	return moduleName

def ShowFavorties(iconimage):
	if common.GetAddonSetting("showFavSort") == 'true':
		sortString = common.GetLocaleString(30036) if favSortBy == 0 else common.GetLocaleString(30003)
		name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
		common.addDir(name, "toggleSortingMethod", 15, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30036), common.GetLocaleString(30003))}, isFolder=False)
	favoritesList = common.ReadList(favoritesFile)
	nowEPG = []
	items = []
	i = -1
	for favorite in favoritesList:
		i += 1
		u = common.encode(favorite, "utf-8")
		prms = dict(common.parse_qsl(u[u.find('?')+1:]))
		url = common.unquote_plus(prms.get('url', ''))
		mode = int(prms.get('mode','-1'))
		name = common.unquote_plus(prms.get('name', '')).replace('|||', '?')
		unColorName = common.GetUnColor(name)
		catName = common.unquote_plus(prms.get('catName', '')).replace('|||', '?')
		image = common.unquote_plus(prms.get('iconimage', ''))
		module = prms.get('module')
		moreData = common.unquote_plus(prms.get('moredata', ''))
		isFolder = prms.get('isFolder', 'False') == 'True'
		isPlayable = prms.get('isPlayable', 'False') == 'True'
		tvgID = prms.get('tvgID', '')
		contextMenu = [(common.GetLocaleString(30027), 'RunPlugin({0}?url={1}&mode=9)'.format(sys.argv[0], i))]
		if favSortBy == 0:
			contextMenu.append((common.GetLocaleString(30031), 'RunPlugin({0}?mode=11&url={1}&moredata=-1)'.format(sys.argv[0], i)))
			contextMenu.append((common.GetLocaleString(30032), 'RunPlugin({0}?mode=11&url={1}&moredata=1)'.format(sys.argv[0], i)))
			contextMenu.append((common.GetLocaleString(30033), 'RunPlugin({0}?mode=11&url={1}&moredata=0)'.format(sys.argv[0], i)))
		if tvgID != '':
			if nowEPG == []:
				nowEPG = epg.GetNowEPG()
			programs = nowEPG.get(tvgID, [])
			items.append((unColorName, common.GetUnColor(name), url, mode, image, module, contextMenu, moreData, programs, isFolder, isPlayable, True))
		else:
			moduleName = GetModuleName(module, mode, moreData, catName)
			if moduleName != '':
				name = '{0} - {1}'.format(common.GetLabelColor(moduleName, keyColor='timesColor', bold=True), name)
			items.append((unColorName, name, url, mode, image, module, contextMenu, moreData, [], isFolder, isPlayable, False))
	if favSortBy == 1:
		items = sorted(items,key=lambda items: items[0])
	for unColorName, name, url, mode, image, module, contextMenu, moreData, programs, isFolder, isPlayable, isLive in items:
		if isLive:
			LiveChannel(name, url, mode, image, module, contextMenu=contextMenu, bitrate=moreData, programs=programs, addFav=False)
		else:
			common.addDir(name, url, mode, image, infos={"Title": name}, contextMenu=contextMenu, moreData=moreData, module=module, isFolder=isFolder, isPlayable=isPlayable, addFav=False)

def Search(searchText=''):
	series = common.GetUpdatedList(common.seriesFile, common.seriesUrl, isZip=True, sort=True)
	filteredSeries = []
	seriesLinks = []
	if searchText == '':
		searchText = common.GetKeyboardText('מילים לחיפוש', '').strip().lower()
	if searchText != '':
		for serie in series:
			if serie['name'].lower().startswith(searchText):
				filteredSeries.append(serie)
				seriesLinks.append(serie['name'])
		for serie in series:
			if searchText in serie['name'].lower() and serie['name'] not in seriesLinks:
				filteredSeries.append(serie)
				seriesLinks.append(serie['name'])
	programNameFormat = int(common.GetAddonSetting("programNameFormat"))
	for serie in filteredSeries:
		serieMoreData = serie.get('moreData', '')
		serieCatName = serie.get('catName', '')
		serieName = serie['name']
		moduleName = GetModuleName(serie['module'], serie['mode'], serieMoreData, serieCatName)
		name = common.getDisplayName(serieName, moduleName, programNameFormat, bold=True)
		infos = {"Title": name, "Plot": serie['desc']}
		isFolder = False if serieMoreData == 'youtube' else True
		common.addDir(name, serie['url'], serie['mode'], common.encode(serie['icon'], 'utf-8'), infos, module=serie['module'], moreData=common.encode(serieMoreData, 'utf-8'), totalItems=len(filteredSeries), isFolder=isFolder, urlParamsData={'name': common.GetLabelColor(serieName, keyColor="prColor", bold=True)})

def PlayLive(id):
	channel = None
	channels = baseChannels.TvChannels + baseChannels.RadioChannels
	for ch in channels:
		if ch.get('ch') == id: 
			channel = ch
			break
	if channel is None:
		return
	nowEPG = epg.GetNowEPG()
	programs = [] if channel.get('tvgID', '') == '' else nowEPG.get(channel['tvgID'], [])
	displayName = common.GetLabelColor(common.GetLocaleString(channel['nameID']), keyColor="chColor", bold=True)
	iconimage = common.GetIconFullPath(channel['image'])
	
	if len(programs) > 0:
		programTime = common.GetLabelColor("[{0}-{1}]".format(datetime.datetime.fromtimestamp(programs[0]["start"]).strftime('%H:%M'), datetime.datetime.fromtimestamp(programs[0]["end"]).strftime('%H:%M')), keyColor="timesColor")
		programName = common.GetLabelColor(common.encode(programs[0]["name"], 'utf-8'), keyColor="prColor", bold=True)
		displayName = GetChannelName(programName, programTime, displayName, channelNameFormat)
	if channel.get('resKey', '') == '':
		bitrate = 'best'
	else:
		bitrate = common.GetAddonSetting(channel['resKey'])
		if bitrate == '':
			bitrate = 'best'
	try:
		module = channel['module']
		moduleScript = __import__('resources.lib.{0}'.format(module), fromlist=[module])
		moduleScript.Run(displayName, channel['channelID'], channel['mode'], iconimage, bitrate)
	except Exception as ex:
		xbmc.log(str(ex), 3)

def SetAutoPlayChannel(name, type):
	is_startup_ch = type == 'tv'
	startup_id = 'startup_ch' if is_startup_ch else 'startup_rd'
	startup_name = common.Addon.setSettingString(id = startup_id, value = name)
	common.Addon.setSettingBool(id = 'is_startup_ch', value = is_startup_ch)
	common.Addon.setSettingBool(id = 'is_startup_rd', value = not is_startup_ch)
	xbmc.executebuiltin("Container.Refresh()")
	
def DisableAutoPlayChannel(type):
	is_startup_id = 'is_startup_ch' if type == 'tv' else 'is_startup_rd'
	common.Addon.setSettingBool(id = is_startup_id, value = False)
	xbmc.executebuiltin("Container.Refresh()")

def route(query):
	global favSortBy, channelNameFormat
	favSortBy	= int(common.GetAddonSetting("favSortBy"))
	channelNameFormat = int(common.GetAddonSetting("channelNameFormat"))
	params = dict(common.parse_qsl(query.replace('?','')))
	url = common.unquote_plus(params.get('url', ''))
	mode = int(params.get('mode','-1'))
	name = common.unquote_plus(params.get('name', '')).replace('|||', '?')
	iconimage = common.unquote_plus(params.get('iconimage', ''))
	module = params.get('module')
	if module == 'twenty':
		module = '14tv'
	moreData = common.unquote_plus(params.get('moredata', ''))
	if module is None:
		if mode == -1:
			GetCategoriesList()
		elif mode == 1:
			LiveChannels()
		elif mode == 2:
			VODs()
		elif mode == 3:
			Radios()
		elif mode == 12:
			RadioVODs()
		elif mode == 4:
			Search(url)
		elif mode == 5:
			PlayLive(url)
		elif mode == 6:
			p = moreData.split(';')
			xbmc.executebuiltin('{0}({1})'.format(url, p[0]))
			if p[-1] != 'noexit':
				sys.exit()
		elif mode == 7:
			MakeIPTVfiles()
			sys.exit()
		elif mode == 8:
			AddFavorite(url)
			sys.exit()
		elif mode == 9:
			RemoveFavortie(int(url))
			sys.exit()
		elif mode == 10:
			ShowFavorties(iconimage)
		elif mode == 11:
			common.MoveInList(int(url), int(moreData), favoritesFile)
		elif mode == 15:
			common.ToggleSortMethod('favSortBy', favSortBy)
		elif mode == 13:
			Podcasts()
		elif mode == 14:
			Musics()
		elif mode == 16:
			from resources.lib import cache
			cache.clear(['pages'])
			xbmc.executebuiltin("Notification({0}, {1}, 5000, {2})".format(AddonName, common.GetLocaleString(32005), icon))
		elif mode == 17:
			SetAutoPlayChannel(name, moreData)
		elif mode == 18:
			DisableAutoPlayChannel(moreData)
		elif mode == 19:
			common.GetChannelsLinks("", "", downloadOnly=True)
		if mode == 1 or mode == 3 or mode == 10:
			common.SetViewMode('episodes')
	else:
		try:
			moduleScript = __import__('resources.lib.{0}'.format(module), fromlist=[module])
			moduleScript.Run(name, url, mode, iconimage, moreData)
		except Exception as ex:
			xbmc.log(str(ex), 3)
			import traceback
			ex_type, ex, tb = sys.exc_info()
			xbmc.log(str(ex_type), 3)
			del tb

	xbmcplugin.endOfDirectory(common.GetHandle())