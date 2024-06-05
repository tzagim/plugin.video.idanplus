# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import os, io, sys, time, datetime, glob, re
import resources.lib.common as common

module = 'iptv'
m3uFile = os.path.join(common.profileDir, 'idanplus.m3u')
xmlFile = os.path.join(common.profileDir, 'epg.xml')

def MakeIPTVlist(channels):
	if common.GetAddonSetting('useIPTV') != 'true':
		return
	iptvList = '#EXTM3U\n'
	timeshift  = '' if common.GetAddonSetting('useIPTVtimeshift') != 'true' else '\n#KODIPROP:inputstream=inputstream.ffmpegdirect\n#KODIPROP:inputstream.ffmpegdirect.stream_mode=timeshift\n#KODIPROP:inputstream.ffmpegdirect.is_realtime_stream=true\n#KODIPROP:mimetype=video/mp2t'
	for channel in channels:
		try:
			type = channel.get('type', '')
			if type != 'radio' and type != 'tv':
				continue
			tvg_id = channel["tvgID"]
			view_name = common.GetLocaleString(channel['nameID'])
			tvg_logo = 'special://home/addons/{0}/resources/images/{1}'.format(common.AddonID, channel['image'])
			if type == 'radio':
				radio = ' radio="true"'
				group = ' group-title="Radio"'
			elif type == 'tv': 
				radio = ''
				group = ' group-title="TV"'
			url = '{0}?mode=5&url={1}'.format(sys.argv[0], channel['ch'])
			iptvList += '{0}\n#EXTINF:-1 tvg-id="{1}"{2} tvg-logo="{3}"{4},{5}\n{6}\n'.format(timeshift, tvg_id, group, tvg_logo, radio, view_name, url)
		except Exception as ex:
			xbmc.log("{0}".format(ex), 3)
	iptvListOld = ''
	if os.path.isfile(m3uFile):
		with io.open(m3uFile, 'r', encoding="utf-8") as f:
			iptvListOld = f.read()
	if iptvListOld != iptvList:
		with io.open(m3uFile, 'w', encoding="utf-8") as f:
			f.write(common.uni_code(iptvList))

def GetTZtime(timestamp):
	ts = time.time()
	tz = timeZone
	if tz == '':
		delta = datetime.datetime.fromtimestamp(ts) - datetime.datetime.utcfromtimestamp(ts)
	else:
		tz = float(tz)
		delta = datetime.timedelta(hours=-tz) * -1 if tz < 0 else datetime.timedelta(hours=tz)
	hrs = '+0000'
	if delta > datetime.timedelta(0):
		hrs = '+{0:02d}{1:02d}'.format(delta.seconds//3600, (delta.seconds//60)%60)
	else:
		delta = -delta
		hrs = '-{0:02d}{1:02d}'.format(delta.seconds//3600, (delta.seconds//60)%60)
	return '{0} {1}'.format(time.strftime('%Y%m%d%H%M%S', time.localtime(timestamp)), hrs)

def MakeChannelsGuide():
	global timeZone
	timeZone = common.GetAddonSetting('timeZone')
	if common.GetAddonSetting('useIPTV') != 'true':
		return
	channelsList = ""
	programmeList = ""
	epgList = common.ReadList(common.epgFile)
	if len(epgList) == 0:
		return
	for key,val in common.items(epgList):
		chName = common.encode(key, "utf-8")
		channelsList += "\t<channel id=\"{0}\">\n\t\t<display-name>{1}</display-name>\n\t</channel>\n".format(common.EscapeXML(chName), chName)
		for programme in val:
			start = GetTZtime(programme["start"])
			end = GetTZtime(programme["end"])
			name = common.EscapeXML(common.encode(programme["name"], "utf-8")) if programme["name"] != None else ""
			description = common.EscapeXML(common.encode(programme["description"], "utf-8")) if programme["description"] != None else ""
			programmeList += "\t<programme start=\"{0}\" stop=\"{1}\" channel=\"{2}\">\n\t\t<title>{3}</title>\n\t\t<desc>{4}</desc>\n\t</programme>\n".format(start, end, common.EscapeXML(chName), name, description)
	xmlList = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<tv>\n{0}{1}</tv>".format(channelsList, programmeList)
	with io.open(xmlFile, 'w', encoding="utf-8") as f:
		f.write(common.uni_code(xmlList))

def EnableIptvClient():
	try:
		if not common.IsAddonInstalled('pvr.iptvsimple'):
			common.InstallAddon('pvr.iptvsimple')
		if not common.IsAddonEnabled('pvr.iptvsimple'):
			common.EnableAddon('pvr.iptvsimple')
		return True
	except Exception as ex:
		xbmc.log("{0}".format(ex), 3)
	return False

def OpenIptvClientSettings():
	if EnableIptvClient():
		xbmc.executebuiltin('Addon.OpenSettings(pvr.iptvsimple)')

def SetIptvClientSettings():
	if EnableIptvClient():
		settings = {
			"m3uPathType": "0",
			"m3uPath": os.path.join(common.Addon.getAddonInfo("profile"),'idanplus.m3u'),
			"epgPathType": "0",
			"epgPath": os.path.join(common.Addon.getAddonInfo("profile"),'epg.xml')
		}
		iptvAddon = xbmcaddon.Addon('pvr.iptvsimple')
		kodiVer = common.GetKodiVer()
		if kodiVer >= 20:
			iptvAddonProfileDir = common.decode(common.translatePath(iptvAddon.getAddonInfo("profile")), "utf-8")
			settingsFiles = sorted(glob.glob(os.path.join(iptvAddonProfileDir, 'instance-settings-*.xml')), reverse=True)
			settingsFile = settingsFiles[0]
			j = settingsFile.rfind('.')
			i = settingsFile[:j].rfind('-')
			index = int(settingsFile[i+1:j])
			settingsNewFile = '{0}{1}{2}'.format(settingsFile[:i+1], str(index+1), settingsFile[j:])
			content = common.GetTextFile(settingsFile)
			for sFile in settingsFiles:
				theFile = True
				for key, val in common.items(settings):
					patern = '<setting id="{0}".*?>(.*?)</setting>'.format(key)
					oldVal = re.compile(patern).findall(content)
					if len(oldVal) < 1:
						patern = '<setting id="{0}".*?/>'.format(key)
						oldVal = re.compile(patern).findall(content)
					else:
						oldVal = oldVal[0]
					if oldVal != val:
						theFile = False
						break
				if theFile == True:
					settingsNewFile = sFile
					settingsFile = sFile
					content = common.GetTextFile(settingsFile)
					break

			settings["kodi_addon_instance_name"] = "Idan+ Plus"
			settings["kodi_addon_instance_enabled"] = "true"

			isChange = False
			for key, val in common.items(settings):
				patern = '<setting id="{0}".*?>(.*?)</setting>'.format(key)
				a = re.compile(patern).findall(content)
				if len(a) < 1:
					patern = '<setting id="{0}".*?/>'.format(key)
					a = re.compile(patern).findall(content)
				else:
					a = a[0]
				l = re.search(patern, content)
				if a != val:
					content = content.replace(content[l.start():l.end()], '<setting id="{0}" default="true">{1}</setting>'.format(key, val))
					isChange = True

			if isChange == True:
				with io.open(settingsNewFile, 'w', encoding="utf-8") as f:
					f.write(common.uni_code(content))
		else:
			for key, val in common.items(settings):
				if iptvAddon.getSetting(key) != val:
					iptvAddon.setSetting(key, val)
		if kodiVer >= 18:
			common.DisableAddon('pvr.iptvsimple')
			common.EnableAddon('pvr.iptvsimple')

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 1:
		MakeIPTVlist(moreData)
	elif mode == 2:
		MakeChannelsGuide()
	elif mode == 3:
		OpenIptvClientSettings()
		sys.exit()
	elif mode == 4:
		SetIptvClientSettings()
		sys.exit()
	common.SetViewMode('episodes')