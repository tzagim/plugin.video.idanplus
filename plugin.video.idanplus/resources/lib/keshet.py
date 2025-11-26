# -*- coding: utf-8 -*-
import xbmc, xbmcplugin
import sys, uuid, re, json, time
import resources.lib.common as common
from resources.lib import cache as cache

module = 'keshet'
moduleIcon = common.GetIconFullPath("mako.png")
baseUrl = 'https://www.mako.co.il'
endings = 'platform=responsive'
entitlementsServices = 'https://mass.mako.co.il/ClicksStatistics/entitlementsServicesV2.jsp'
da = '6gkr2ks9-4610-392g-f4s8-d743gg4623k2'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def GetJson(url):
	headers = {
		"User-Agent": UA,
		"Accept": "application/json, text/plain, */*",
		"Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
		"Accept-Encoding": "gzip, deflate, br",
		"Referer": "https://www.mako.co.il/",
		"Origin": "https://www.mako.co.il",
		"Connection": "keep-alive",
		"Sec-Fetch-Dest": "empty",
		"Sec-Fetch-Mode": "cors",
		"Sec-Fetch-Site": "same-origin"
	}
	resultJSON = common.OpenURL(url, headers=headers, responseMethod='json')
	if resultJSON is None or len(resultJSON) < 1:
		return None
	if "root" in resultJSON:
		return resultJSON["root"]
	else:
		return resultJSON

def GetJsonSection(url):
	try:
		# Add small delay to avoid being blocked
		# time.sleep(0.5)
		
		headers = {
			"User-Agent": UA,
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
			"Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
			"Accept-Encoding": "gzip, deflate, br",
			"Referer": "https://www.mako.co.il/",
			"Connection": "keep-alive",
			"Upgrade-Insecure-Requests": "1",
			"Sec-Fetch-Dest": "document",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "same-origin"
		}
		html = common.OpenURL(url, headers=headers)
		if html is None or html == "":
			xbmc.log("GetJsonSection: No HTML content received from URL: {0}".format(url), xbmc.LOGERROR)
			return None
		
		# Try multiple regex patterns to find JSON data
		patterns = [
			r'type="application/json">(.*?)</script>',
			r'"application/json">(.*?)</script>',
			r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
			r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
		]
		
		for pattern in patterns:
			match = re.compile(pattern, re.DOTALL).findall(html)
			if match and len(match) > 0:
				try:
					json_data = json.loads(match[0])
					xbmc.log("GetJsonSection: Successfully parsed JSON from URL: {0}".format(url), 1)
					return json_data
				except json.JSONDecodeError as e:
					xbmc.log("GetJsonSection: JSON decode error for pattern {0}: {1}".format(pattern, str(e)), xbmc.LOGERROR)
					continue
		
		xbmc.log("GetJsonSection: No valid JSON found in HTML from URL: {0}".format(url), xbmc.LOGERROR)
		return None
		
	except Exception as ex:
		xbmc.log("GetJsonSection: Exception occurred: {0}".format(str(ex)), xbmc.LOGERROR)
		return None
	
def GetApiVer(url):
	resultJSON = GetJsonSection(url)

	if resultJSON is None or len(resultJSON) < 1:
		return None
	return resultJSON.get("buildId")

def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 7, iconimage, infos={"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	#name = "חיפוש"
	#common.addDir(name, "{0}/autocomplete/vodAutocompletion.ashx?query={{0}}&max=60&id=query".format(baseUrl), 6, common.GetIconFullPath('search.jpg'), infos={"Title": name, "Plot": "חיפוש"}, module=module)
	resultJSON = GetJsonSection("{0}/mako-vod-index".format(baseUrl))
	if resultJSON is None or len(resultJSON) < 1:
		return	
	for menuItem in resultJSON.get("props", {}).get("pageProps", {}).get("menuPrograms", {}).get("menuItems", []):
		name = common.GetLabelColor(menuItem["title"], bold=True, color="none")
		common.addDir(name, "{0}{1}".format(baseUrl, menuItem["url"]), 1, iconimage, infos={"Title": name}, module=module)

#'''
def GetSeriesList(url, iconimage):
	url = "{0}&{1}".format(url, endings) if "?" in url else "{0}?{1}".format(url, endings)
	#prms = GetJson(url)
	prms = cache.get(GetJson, 72, url, table='pages')
	if prms==[]:
		prms = cache.get(GetJson, 0, url, table='pages')
	if prms is None:
		"Cannot get list for url {0}".format(url)
		return
	series = prms.get('items', {})
	seriesCount = len(series)
	for serie in series:
		try:
			title = common.GetLabelColor(common.encode(serie.get("title", "").strip(), "utf-8"), keyColor="prColor", bold=True)
			url = "{0}{1}".format(baseUrl, serie.get("pageUrl", ""))
			icon = serie.get("pic", "")
			infos = {"Title": title, "Plot": title, 'mediatype': 'movie'}
			common.addDir(title, url, 2, icon, infos, module=module, totalItems=seriesCount)
		except Exception as ex:
			xbmc.log(str(ex), xbmc.LOGERROR)
	if sortBy == 1:
		xbmcplugin.addSortMethod(common.GetHandle(), xbmcplugin.SORT_METHOD_LABEL)
#'''

def GetProgramUrl(url):
	try:
		#urlParts = url[len(baseUrl)+1:].split("/")
		if len(url) < 9:
			xbmc.log("GetProgramUrl: Invalid URL format: {0}".format(url), xbmc.LOGERROR)
			return None
			
		i = url[8:].find("/")
		if i == -1:
			xbmc.log("GetProgramUrl: Could not find path separator in URL: {0}".format(url), xbmc.LOGERROR)
			return None
			
		urlParts = url.lower()[9+i:].split("/")
		if len(urlParts) < 2:
			xbmc.log("GetProgramUrl: Invalid URL parts: {0}".format(urlParts), xbmc.LOGERROR)
			return None
			
		buildId = GetApiVer(url)
		currentBuildId = common.GetAddonSetting("MakoBuildId")
		if buildId is None:
			buildId = currentBuildId
			if buildId is None or buildId == "":
				xbmc.log("GetProgramUrl: No build ID available for URL: {0}".format(url), xbmc.LOGERROR)
				return None
		elif buildId != currentBuildId:
			common.SetAddonSetting("MakoBuildId", buildId)
			
		programUrl = "{0}/_next/data/{1}/{{0}}/{{1}}.json?mako_vod_channel={{0}}&program={{1}}".format(baseUrl, buildId)
		return programUrl.format(urlParts[0], urlParts[1])
		
	except Exception as ex:
		xbmc.log("GetProgramUrl: Exception occurred: {0}".format(str(ex)), xbmc.LOGERROR)
		return None

def GetSeasonsList(url, iconimage):
	try:
		#data = GetJson(GetProgramUrl(url))["pageProps"]["data"]
		programUrl = GetProgramUrl(url)
		if programUrl is None:
			xbmc.log("GetSeasonsList: Failed to get program URL for: {0}".format(url), xbmc.LOGERROR)
			return
			
		cached_data = cache.get(GetJson, 24, programUrl, table='pages')
		if cached_data is None or cached_data == []:
			cached_data = cache.get(GetJson, 0, programUrl, table='pages')
			if cached_data is None:
				xbmc.log("GetSeasonsList: Failed to get data from cache for URL: {0}".format(programUrl), xbmc.LOGERROR)
				return
		
		if "pageProps" not in cached_data or "data" not in cached_data["pageProps"]:
			xbmc.log("GetSeasonsList: Invalid data structure for URL: {0}".format(programUrl), xbmc.LOGERROR)
			return
			
		data = cached_data["pageProps"]["data"]
		
		#if iconimage == common.GetIconFullPath('search.jpg'):
		if "seo" in data and "image" in data["seo"]:
			iconimage = data["seo"]["image"]
			
		seasons = data.get("seasons", [])
		if len(seasons) < 1:
			GetEpisodesList(url, iconimage, data)
			return
			
		grids_arr = []
		index = 0
		for season in seasons:
			try:
				name = common.GetLabelColor(common.encode(season.get('seasonTitle', ''), "utf-8"), keyColor="timesColor", bold=True)
				url = "{0}{1}".format(baseUrl, season["pageUrl"])
				grids_arr.append((index, name, url))
				index += 1
			except Exception as ex:
				xbmc.log("GetSeasonsList: Error processing season: {0}".format(str(ex)), xbmc.LOGERROR)
				
		grids_sorted = sorted(grids_arr,key=lambda grids_arr: grids_arr[0], reverse=True)
		for index, name, link in grids_sorted:
			common.addDir(name, link, 3, iconimage, infos={"Title": name, "Plot": name}, module=module)
			
	except Exception as ex:
		xbmc.log("GetSeasonsList: Exception occurred: {0}".format(str(ex)), xbmc.LOGERROR)

def GetEpisodesList(url, icon, data=None):
	if data is None:
		# data = cache.get(GetJson, 24, GetProgramUrl(url), table='pages')["pageProps"]["data"]
		data = GetJson(GetProgramUrl(url))["pageProps"]["data"]
	videoChannelId = data["channelId"]
	isEpisodes = False
	for menu in data["menu"]:
		if menu is None or "vods" not in menu:
			continue
		buttonText = common.encode(menu["buttonText"], "utf-8")
		common.addDir('------- {0} -------'.format(common.GetLabelColor(buttonText, keyColor="timesColor", bold=True)), buttonText, 99, icon, isFolder=False)
		grids_arr = []
		for vod in menu["vods"]:
			try:
				if vod["componentLayout"] != "vod":
					continue
				isEpisodes = True
				vcmid = vod["itemVcmId"]
				title = vod["title"]
				subtitle = vod.get("extraInfo", "").replace("@", " * ")
				if subtitle == "":
					subtitle = vod.get ("subtitle", "")
					name = common.getDisplayName(common.encode(title, "utf-8"), common.encode(subtitle, "utf-8"), programNameFormat) if makoShowShortSubtitle else common.GetLabelColor(common.encode(title, "utf-8"), keyColor="prColor", bold=False)
				else:
					name = common.getDisplayName(common.encode(subtitle, "utf-8"), common.encode(title, "utf-8"), programNameFormat) if makoShowShortSubtitle else common.GetLabelColor(common.encode(subtitle, "utf-8"), keyColor="prColor", bold=False)
				url = "{0}/VodPlaylist?vcmid={1}&videoChannelId={2}".format(baseUrl, vcmid, videoChannelId)
				iconimage = vod["pics"][0]["picUrl"]
				infos = {"Title": name, "Plot": name}
				common.addDir(name, url, 4, iconimage, infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_mako_res&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module))], moreData=bitrate, module=module, isFolder=False, isPlayable=True)
			except Exception as ex:
				xbmc.log(str(ex), xbmc.LOGERROR)
	if isEpisodes == False:
		vod = data.get("vod") 
		if vod != None:
			vcmid = vod["itemVcmId"]
			title = data["seo"]["title"]
			subtitle = data["seo"]["description"]
			name = common.getDisplayName(common.encode(subtitle, "utf-8"), common.encode(title, "utf-8"), programNameFormat) if makoShowShortSubtitle else common.GetLabelColor(common.encode(subtitle, "utf-8"), keyColor="prColor", bold=False)
			url = "{0}/VodPlaylist?vcmid={1}&videoChannelId={2}".format(baseUrl, vcmid, videoChannelId)
			iconimage = data["seo"]["image"]
			infos = {"Title": name, "Plot": name}
			common.addDir(name, url, 4, iconimage, infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_mako_res&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module))], moreData=bitrate, module=module, isFolder=False, isPlayable=True)

def GetChannels(url, iconimage):
	headers = {
		"User-Agent": UA,
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
		"Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
		"Accept-Encoding": "gzip, deflate, br",
		"Referer": "https://www.mako.co.il/",
		"Connection": "keep-alive",
		"Upgrade-Insecure-Requests": "1"
	}
	html = common.OpenURL(url, headers=headers)
	if html == "":
		return None
	match = re.compile("var makoliveJson ='(.*?)';").findall(html)
	resultJSON = json.loads(match[0])
	if resultJSON is None or len(resultJSON) < 1:
		return None
	for channel in resultJSON['list']:
		name = common.GetLabelColor(common.encode(channel['title'], "utf-8"), keyColor="prColor")
		infos = {"Title": name, "Plot": common.encode(channel['subtitle'], "utf-8")}
		url = '{0}{1}'.format(baseUrl, channel['link'])
		iconimage = channel['picUrl']
		common.addDir(name, url, 5, iconimage, infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=5&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module))], moreData=bitrate, module=module, isFolder=False, isPlayable=True)

def WatchLive(url, name='', iconimage='', quality='auto'):
	channels = common.GetChannelsLinks("tv", module)
	headers = {
		"User-Agent": UA
	}
	url = channels[url]
	ticket = GetTicket('{0}?et=ngt&lp={1}&rv=AKAMAI'.format(entitlementsServices, url), headers)
	pos = url.find('?');
	if pos > 0:
		url = url[:pos]
	link = 'https://mako-streaming.akamaized.net{0}?{1}'.format(url, ticket)
	if quality != 'auto':
		link = common.GetStreams(link, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, UA)
	common.PlayStream(final, quality, name, iconimage)

def PlayItem(url, name='', iconimage='', quality='auto', swichCdn=False):
	prms = GetJson("{0}?{1}".format(url, endings))
	if prms is None or len(prms) < 1:
		return None
	iconimage = prms["seo"]["image"]
	videoChannelId=prms["vod"]["channelId"]
	vcmid = prms["vod"]["itemVcmId"]
	url = "vcmid={0}&videoChannelId={1}".format(vcmid,videoChannelId)
	Play(url, name, iconimage, quality, swichCdn=swichCdn)

def Play(url, name='', iconimage='', quality='auto', swichCdn=False):
	common.DelCookies()
	headers = {
		"User-Agent": UA,
		"Accept": "application/json, text/plain, */*",
		"Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
		"Accept-Encoding": "gzip, deflate, br",
		"Referer": "https://www.mako.co.il/",
		"Origin": "https://www.mako.co.il",
		"Connection": "keep-alive",
		"Sec-Fetch-Dest": "empty",
		"Sec-Fetch-Mode": "cors",
		"Sec-Fetch-Site": "same-origin"
	}
	dv = url[url.find('vcmid=')+6: url.find('&videoChannelId=')]
	ch = url[url.find('&videoChannelId=')+16:]
	media = common.OpenURL('{0}/AjaxPage?jspName=playlist.jsp&vcmid={1}&videoChannelId={2}&galleryChannelId={1}&isGallery=false&consumer=web_html5&encryption=no'.format(baseUrl, dv, ch), headers=headers, responseMethod='json')['media']
	cdns = ['AKAMAI', 'AWS'] if swichCdn else ['AWS', 'AKAMAI']
	link, cookie_jar = GetLink(media, cdns[0], dv, headers, quality)
	if link is None:
		link, cookie_jar = GetLink(media, cdns[1], dv, headers, quality)
		if link is None:
			return None
	#cookies = ";".join(['{0}'.format(common.quote('{0}={1}'.format(_cookie.name, _cookie.value))) for _cookie in cookie_jar])
	#final = '{0}|User-Agent={1}&Cookie={2}'.format(link, UA, cookies)
	final = '{0}|User-Agent={1}'.format(link, UA)
	common.PlayStream(final, quality, name, iconimage)

def GetLink(media, cdn, dv, headers, quality):
	url = ''
	media = sorted(media,key=lambda media: int(media["cdnLB"]), reverse=True)
	#media = sorted(media,key=lambda media: int(media["cdnLB"]))
	for item in media:
		if item['cdn'] == cdn.upper():
			url = item['url']
			if cdn.upper() == 'AKAMAI':
				pos = url.find('?');
				if pos > 0:
					url = url[:pos]
			break
	if url == '':
		return None, None
	if username.strip() == '':
		l = '{0}?et=gt&lp={1}&rv={2}'.format(entitlementsServices, url, cdn)
	else:
		l = '{0}?et=gt&na=2.0&da{1}=&du={2}&dv={3}&rv={4}&lp={5}'.format(entitlementsServices, da, deviceID, dv, cdn, url)
	ticket = GetTicket(l, headers)
	if url.startswith('//'):
		url = 'https:{0}'.format(url) 
	if quality == 'auto':
		return '{0}&{1}'.format(url, ticket) if '?' in url else '{0}?{1}'.format(url, ticket), None		   
	session = common.GetSession()
	link = common.GetStreams('{0}&{1}'.format(url, ticket) if '?' in url else '{0}?{1}'.format(url, ticket), headers=headers, session=session, quality=quality)
	return link, session.cookies

def GetTicket(link, headers):
	# Add additional headers for ticket request
	ticket_headers = headers.copy()
	ticket_headers.update({
		"Accept": "application/json, text/plain, */*",
		"Referer": "https://www.mako.co.il/",
		"Origin": "https://www.mako.co.il"
	})
	text = common.OpenURL(link, headers=ticket_headers)
	result = json.loads(text)
	if result['caseId'] == '4':
		result = Login()
		text = common.OpenURL(link, headers=headers)
		result = json.loads(text)
		if result['caseId'] != '1':
			xbmc.executebuiltin("Notification({0}, You need to pay if you want to watch this video., {1}, {2})".format(common.AddonName, 5000 ,common.icon))
			return
	elif result['caseId'] != '1':
		xbmc.executebuiltin("Notification({0}, Cannot get access for this video., {1}, {2})".format(common.AddonName, 5000 ,common.icon))
		return
	return common.unquote_plus(result['tickets'][0]['ticket'])

def Login():
	headers = {
		"User-Agent": UA,
		"Accept": "application/json, text/plain, */*",
		"Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
		"Accept-Encoding": "gzip, deflate, br",
		"Referer": "https://www.mako.co.il/",
		"Origin": "https://www.mako.co.il",
		"Connection": "keep-alive"
	}
	text = common.OpenURL('{0}?eu={1}&da={2}&dwp={3}&et=ln&du={4}'.format(entitlementsServices, username, da, password, deviceID), headers=headers)
	result = json.loads(text)
	if result['caseId'] != '1':
		return result
	text = common.OpenURL('{0}?da={1}&et=gds&du={2}'.format(entitlementsServices, da, deviceID), headers=headers)
	return json.loads(text)

def Search(url, iconimage):
	search_entered = common.GetKeyboardText('מילים לחיפוש', '')
	if search_entered != '':
		url = url.format(search_entered.replace(' ', '%20'))
		params = GetJson(url)
		suggestions = params["suggestions"]
		data = params["data"]
		for i in range(len(suggestions)):
			if "mako-vod-channel2-news" in data[i]:
				continue
			url = "{0}{1}".format(baseUrl, data[i])
			name = common.UnEscapeXML(common.encode(suggestions[i], "utf-8"))
			infos={"Title": name, "Plot": name}
			if "VOD-" in data[i]:
				name = common.GetLabelColor(name, keyColor="chColor")
				common.addDir(name, url, 5, iconimage, infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=5&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module))], moreData=bitrate, module=module, isFolder=False, isPlayable=True)
			else:
				name = common.GetLabelColor(name, keyColor="prColor", bold=True)
				common.addDir(name, url, 2, iconimage, infos, module=module)
	else:
		return

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy, bitrate, programNameFormat, deviceID, username, password, makoShowShortSubtitle
	sortBy = int(common.GetAddonSetting('makoSortBy'))
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	programNameFormat = int(common.GetAddonSetting("programNameFormat"))
	#deviceID = common.GetAddonSetting("makoDeviceID")
	#if deviceID.strip() == '':
	#	uuidStr = str(uuid.uuid1()).upper()
	#	deviceID = "W{0}{1}".format(uuidStr[:8], uuidStr[9:])
	#	common.SetAddonSetting("makoDeviceID", deviceID)
	uuidStr = str(uuid.uuid1()).upper()
	deviceID = "W{0}{1}".format(uuidStr[:8], uuidStr[9:])
	username = common.GetAddonSetting("makoUsername")
	password = common.GetAddonSetting("makoPassword")
	makoShowShortSubtitle = common.GetAddonSetting("makoShowShortSubtitle") == 'true'
	
	if mode == 0:
		GetCategoriesList(moduleIcon)
	elif mode == 1:	#------------- Series: -----------------
		#GetSeriesList(common.GetUnColor(name), url, iconimage)
		GetSeriesList(url, iconimage)
	elif mode == 2:	#------------- Seasons: -----------------
		GetSeasonsList(url, iconimage)
	elif mode == 3:	#------------- Episodes: -----------------
		GetEpisodesList(url, iconimage)
	elif mode == 4:	#------------- Playing episode  -----------------
		Play(url, name, iconimage, moreData)
	elif mode == 5:	#------------- Playing item: -----------------
		if moreData == '':
			moreData = 'auto'
		PlayItem(url, name, iconimage, moreData)
	elif mode == 6:	#------------- Search items: -----------------
		Search(url, iconimage)
	elif mode == 7:	#------------- Toggle Lists' sorting method: -----------------
		common.ToggleSortMethod('makoSortBy', sortBy)
	elif mode == 8:
		GetChannels(url, iconimage)
	elif mode == 10:
		WatchLive(url, name, iconimage, moreData)
	elif mode == 20:
		ShowYears(iconimage)
	elif mode == 21:
		ShowMonthes(url, iconimage)
		
	common.SetViewMode('episodes')
