# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import sys, uuid, re, json, time, datetime
import resources.lib.common as common
from resources.lib import cache as cache
from resources.lib import watch_store, watch_ui

module = 'keshet'
moduleIcon = common.iconKeshet
baseUrl = 'https://www.mako.co.il'
endings = 'platform=responsive'
entitlementsServices = 'https://mass.mako.co.il/ClicksStatistics/entitlementsServicesV2.jsp'
da = '6gkr2ks9-4610-392g-f4s8-d743gg4623k2'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Header sets of a real Chrome 155 on Windows (copied from a browser's own request to this site; no cookies, no account data): a request that
# carries only some of the headers a real browser sends, or a mix of versions, is what mako's bot filter (Radware) picks on. Reshet 13 uses
# the same kind of set. `browserHeaders` is for the JSON requests, `pageHeaders` for the HTML pages.
UA155 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'
chromeHints = {
	'Sec-Ch-Ua': '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
	'Sec-Ch-Ua-Mobile': '?0',
	'Sec-Ch-Ua-Platform': '"Windows"',
	'User-Agent': UA155,
	'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
	'Accept-encoding': 'gzip, deflate, br',
	'Cache-Control': 'no-cache',
	'Pragma': 'no-cache',
	'DNT': '1',
}
browserHeaders = dict(chromeHints, **{
	'Accept': 'application/json, text/plain, */*',
	'Referer': 'https://www.mako.co.il/',
	'Sec-Fetch-Dest': 'empty',
	'Sec-Fetch-Mode': 'cors',
	'Sec-Fetch-Site': 'same-origin',
})
pageHeaders = dict(chromeHints, **{
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
	'Priority': 'u=0, i',
	'Upgrade-Insecure-Requests': '1',
	'Sec-Fetch-Dest': 'document',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'none',
	'Sec-Fetch-User': '?1',
})

def ReadJson(url, headers):
	"""The JSON answer of `url`, or None. What a failed answer looked like is written to the log (it used to be thrown away, so an
	empty list could not be explained): mako answers a blocked request with an HTML page, or with nothing."""
	text = common.OpenURL(url, headers=headers)
	if not text:
		xbmc.log("keshet GetJson: no answer from {0}".format(url), xbmc.LOGERROR)
		return None
	try:
		return json.loads(text)
	except ValueError:
		xbmc.log("keshet GetJson: not JSON from {0}: {1}".format(url, " ".join(text[:120].split())), xbmc.LOGERROR)
		return None

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
	# the full browser set first: with the partial set above mako answered 503 on 2026-10-23 (PC log 15:20:52) and only the full set got through
	resultJSON = ReadJson(url, dict(browserHeaders))
	if resultJSON is None:
		time.sleep(2)
		resultJSON = ReadJson(url, headers)
	if resultJSON is None or len(resultJSON) < 1:
		return None
	if "root" in resultJSON:
		return resultJSON["root"]
	else:
		return resultJSON

def GetJsonSection(url):
	"""The JSON block embedded in the HTML page `url`, or None. The Chrome 155 page headers go first; when that answer holds no JSON
	(mako's bot filter answers with a block page) the old header set is tried once more after 2 s."""
	oldHeaders = {
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
	section = ReadSection(url, dict(pageHeaders))
	if section is None:
		time.sleep(2)
		section = ReadSection(url, oldHeaders)
	return section

def ReadSection(url, headers):
	try:
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

# The VOD categories as mako listed them on 2026-10-23 (title, page): shown only when mako's page cannot be read and nothing is saved, so the
# list is never empty. They are site ids that change rarely; a fresh or saved copy of the real list always replaces them.
defaultMenuItems = [
	{"title": "כל התכניות", "url": "/mako-vod-index"},
	{"title": "ריאליטי", "url": "/mako-vod-index?filter=genre&vcmId=4f9dbac980653210VgnVCM2000002a0c10acRCRD"},
	{"title": "דוקומנטרי", "url": "/mako-vod-index?filter=genre&vcmId=8e8abac980653210VgnVCM2000002a0c10acRCRD"},
	{"title": "דרמה", "url": "/mako-vod-index?filter=genre&vcmId=05fcbac980653210VgnVCM2000002a0c10acRCRD"},
	{"title": "קומדיה", "url": "/mako-vod-index?filter=genre&vcmId=fe2dbac980653210VgnVCM2000002a0c10acRCRD"},
	{"title": "בישול", "url": "/mako-vod-index?filter=genre&vcmId=5d738481c9674210VgnVCM2000002a0c10acRCRD"},
	{"title": "החדשות", "url": "/mako-vod-index?filter=provider&vcmId=ee06c13070733210VgnVCM2000002a0c10acRCRD"},
	{"title": "פודקאסטים", "url": "/mako-vod-index?filter=provider&vcmId=d5aae64655ea0810VgnVCM100000700a10acRCRD"},
	{"title": "ערוץ 24", "url": "/mako-vod-index?filter=provider&vcmId=3377c13070733210VgnVCM2000002a0c10acRCRD"},
	{"title": "תכניות לפי א'-ב'", "url": "/mako-vod-index?filter=ABC_Programs_Slider"},
	{"title": "פלייליסטים", "url": "/mako-vod-index?filter=playlists"},
]

def GetMenuItems(url):
	"""The VOD menu entries of the page `url` (a few hundred bytes), or None when the page could not be read: only this small
	list is cached, not the page's whole JSON."""
	resultJSON = GetJsonSection(url)
	if resultJSON is None or len(resultJSON) < 1:
		return None
	return resultJSON.get("props", {}).get("pageProps", {}).get("menuPrograms", {}).get("menuItems", []) or None

def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 7, iconimage, infos={"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	#name = "חיפוש"
	#common.addDir(name, "{0}/autocomplete/vodAutocompletion.ashx?query={{0}}&max=60&id=query".format(baseUrl), 6, common.GetIconFullPath('search.jpg'), infos={"Title": name, "Plot": "חיפוש"}, module=module)
	# mako's bot filter (Radware) blocks an address after a few requests and answers with a page that has no JSON: the list
	# is cached like the series lists below, so it is asked for once a day and the last good copy is shown while blocked
	menuItems = cache.get(GetMenuItems, 24, "{0}/mako-vod-index".format(baseUrl), table='pages') or defaultMenuItems
	for menuItem in menuItems:
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
	watchEpisodes = []
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
				watchEpisodes.append(WatchEpisode(vcmid, title, vod.get("extraInfo", ""), iconimage, url))
				common.addDir(name, url, 4, iconimage, infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_mako_res&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module))], moreData=bitrate, module=module, isFolder=False, isPlayable=True, noResume=True)
			except Exception as ex:
				xbmc.log(str(ex), xbmc.LOGERROR)
	if isEpisodes:
		RememberSeason(data, watchEpisodes)
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
			common.addDir(name, url, 4, iconimage, infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_mako_res&module={4})'.format(sys.argv[0], common.quote_plus(url), common.quote_plus(name), common.quote_plus(iconimage), module))], moreData=bitrate, module=module, isFolder=False, isPlayable=True, noResume=True)

def Aired(extraInfo):
	"""The air date `YYYY-MM-DD` of a listing row's "פרק 41@13.05.26" (two- or four-digit year), or '' when there is none or it is not a real date."""
	found = re.search(r'@(\d{1,2})\.(\d{1,2})\.(\d{2,4})', extraInfo or '')
	if not found:
		return ''
	day, month, year = (int(x) for x in found.groups())
	try:
		return datetime.date(year + 2000 if year < 100 else year, month, day).isoformat()
	except ValueError:
		return ''

def WatchEpisode(vcmid, title, extraInfo, iconimage, url):
	"""One episode as the watch history stores it: stable id, plain title, the number from "פרק 41@13.05.26" (None when absent), the air date, picture and play url."""
	found = re.search(r'פרק\s*(\d+)', extraInfo or '')
	return {'key': watch_store.episode_key(module, vcmid), 'name': title, 'icon': iconimage, 'number': int(found.group(1)) if found else None, 'url': url, 'aired': Aired(extraInfo)}

def EpisodeFacts(playlist, dv):
	"""`{episode key: facts}` from the playlist answer of episode `dv`: its own description, air date and length (`videoDetails`) and the description of the next
	episode (Mako's `nextEpisode.externalTitle`, the same text that episode's own answer carries; checked against the real server). Only what is present."""
	facts = {}
	infos = EpisodeInfos(playlist)
	own = {name: infos[source] for name, source in (('plot', 'plot'), ('aired', 'aired'), ('duration', 'duration')) if infos.get(source)}
	if own:
		facts[watch_store.episode_key(module, dv)] = own
	nxt = playlist.get('nextEpisode') if isinstance(playlist, dict) else None
	if isinstance(nxt, dict) and nxt.get('vcmId') and isinstance(nxt.get('externalTitle'), str) and nxt['externalTitle'].strip():
		facts[watch_store.episode_key(module, nxt['vcmId'])] = {'plot': nxt['externalTitle'].strip()}
	return facts

def RememberFacts(dv, playlist):
	"""Save `EpisodeFacts` for the chooser. Local file work only; a failure here must never stop a play."""
	try:
		meta = watch_store.EpisodeMeta(watch_store.watch_folder(common.profileDir))
		for key, facts in EpisodeFacts(playlist, dv).items():
			meta.remember(key, **facts)
	except Exception as ex:
		xbmc.log("keshet RememberFacts: {0}".format(ex), xbmc.LOGERROR)

def RememberSeason(data, episodes):
	"""Save this season's ordered episodes in the watch history (only writes when they changed). A failure here must never break a listing."""
	try:
		seasonUrl = data.get("pageUrl", "")
		seriesKey = re.sub(r'-s\d+$', '', seasonUrl)
		seriesTitle = data.get("seo", {}).get("title", "").split(" - ")[0].strip()
		watch_store.SeasonIndex(watch_store.watch_folder(common.profileDir)).remember_season(seasonUrl, seriesKey, seriesTitle, data.get("channelName", ""), episodes)
	except Exception as ex:
		xbmc.log("keshet RememberSeason: {0}".format(ex), xbmc.LOGERROR)

def EpisodeInfos(playlist):
	"""Video info for the playing item from the `videoDetails` block of the playlist answer Play already fetched (no extra request): the real episode
	title, show, season and episode numbers, plot, air date and length. Only what is present and sensible is returned; `{}` when the block is missing."""
	details = playlist.get('videoDetails') if isinstance(playlist, dict) else None
	if not isinstance(details, dict) or not details:
		return {}
	infos = {'mediatype': 'episode'}
	for key, source in (('title', 'title'), ('tvshowtitle', 'programName'), ('plot', 'desc')):
		text = (details.get(source) or '').strip()
		if text:
			infos[key] = text
	for key, source in (('season', 'season'), ('episode', 'episodeNumber')):
		found = re.search(r'\d+', str(details.get(source) or ''))
		if found:
			infos[key] = int(found.group())
	try:
		infos['aired'] = time.strftime('%Y-%m-%d', time.gmtime(int(details['programStartDate'])))
	except (KeyError, ValueError, TypeError, OverflowError, OSError):
		pass
	try:
		infos['duration'] = int(details['noAdsDuration'])
	except (KeyError, ValueError, TypeError):
		found = re.match(r'^(\d+):(\d\d):(\d\d)$', str(details.get('duration') or ''))
		if found:
			infos['duration'] = int(found.group(1)) * 3600 + int(found.group(2)) * 60 + int(found.group(3))
	return infos

def PromptProps(playlist):
	"""The ListItem property `idanplus_prompt` for the next-episode card, from the same playlist answer: Mako's `creditsTime` (where the credits start)
	with the episode length it refers to, and its `nextEpisode` as a ready entry. Every part is optional and checked; `{}` when nothing is usable
	(the service then uses its own defaults: 30 s before the end, the next row of the saved season)."""
	if not isinstance(playlist, dict):
		return {}
	data = {}
	details = playlist.get('videoDetails') if isinstance(playlist.get('videoDetails'), dict) else {}
	credits = playlist.get('creditsTime')
	if isinstance(credits, (int, float)) and not isinstance(credits, bool) and credits > 0:
		data['credits'] = credits
		try:
			data['total'] = int(details['noAdsDuration'])
		except (KeyError, ValueError, TypeError):
			pass
	nxt = playlist.get('nextEpisode')
	if isinstance(nxt, dict) and nxt.get('vcmId') and nxt.get('channelId'):
		show, season = (details.get('programName') or '').strip(), (details.get('season') or '').strip()
		title = (nxt.get('title') or '').strip()
		prefix = '{0} {1} '.format(show, season)
		name = title[len(prefix):].strip() if show and season and title.startswith(prefix) else title
		if name:
			data['next'] = {
				'key': watch_store.episode_key(module, nxt['vcmId']), 'name': name, 'icon': nxt.get('PictureB') or '', 'number': None, 'series_title': show,
				'url': '{0}/VodPlaylist?vcmid={1}&videoChannelId={2}'.format(baseUrl, nxt['vcmId'], nxt['channelId'])}
	return {'idanplus_prompt': json.dumps(data, ensure_ascii=False)} if data else {}

def ResumeProps(dv):
	"""ListItem properties for playing episode `dv`: its watch-history key (the service reads it back from the playing item)."""
	return {'idanplus_key': watch_store.episode_key(module, dv)}

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

def WatchLive(channelID, name='', iconimage='', quality='auto'):
	channel = common.GetChannel(channelID)
	isAdaptive = common.GetChannelAdaptive(channel)
	linkDetails = channel.get('linkDetails')
	headers = {
		"User-Agent": UA
	}
	url = linkDetails['link']
	host = linkDetails.get('host', 'https://mako-streaming.akamaized.net')
	cdn = linkDetails.get('cdn', 'AKAMAI')
	ticket = GetTicket('{0}?et=ngt&lp={1}&rv={2}'.format(entitlementsServices, url, cdn), headers)
	if ticket is None:
		xbmc.log('WatchLive: no ticket for channel {0} (cdn {1})'.format(channelID, cdn), xbmc.LOGERROR)
		return None
	#pos = url.find('?');
	#if pos > 0:
	#	url = url[:pos]
	link = '{0}{1}&{2}'.format(host, url, ticket) if url.find('?') > 0 else '{0}{1}?{2}'.format(host, url, ticket)
	if quality != 'auto':
		link = common.GetStreams(link, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, UA)
	common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive)

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
	oldHeaders = {
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
	headers = dict(browserHeaders, Origin="https://www.mako.co.il")
	dv = url[url.find('vcmid=')+6: url.find('&videoChannelId=')]
	ch = url[url.find('&videoChannelId=')+16:]
	# the "resume or start over" question (setting watch_resume) comes first: cancelling it costs no request to the site
	proceed, resume = watch_ui.ChooseResume(watch_store.episode_key(module, dv), name, iconimage)
	if not proceed:
		if common.GetHandle() >= 0:   # run as a script (handle -1) nothing waits for an answer: cancelling is quiet
			xbmcplugin.setResolvedUrl(common.GetHandle(), False, xbmcgui.ListItem())
		return None
	playlistUrl = '{0}/AjaxPage?jspName=playlist.jsp&vcmid={1}&videoChannelId={2}&galleryChannelId={1}&isGallery=false&consumer=web_html5&encryption=no'.format(baseUrl, dv, ch)
	playlist = ReadJson(playlistUrl, headers)
	if playlist is None:
		time.sleep(2)
		playlist = ReadJson(playlistUrl, oldHeaders)
	media = playlist.get('media') if isinstance(playlist, dict) else None
	if not media:
		xbmc.log("keshet Play: no playlist for {0}".format(dv), xbmc.LOGERROR)
		return None
	RememberFacts(dv, playlist)
	cdns = ['AKAMAI', 'AWS'] if swichCdn else ['AWS', 'AKAMAI']
	used = cdns[0]
	link, cookie_jar = GetLink(media, cdns[0], dv, headers, quality)
	if link is None:
		used = cdns[1]
		link, cookie_jar = GetLink(media, cdns[1], dv, headers, quality)
		if link is None:
			xbmc.log("keshet Play: no playable stream from {0} or {1} for {2}".format(cdns[0], cdns[1], dv), xbmc.LOGERROR)
			return None
	xbmc.log("keshet Play: {0} from {1}{2}".format(dv, used, "" if used == cdns[0] else " (the first CDN gave nothing)"), xbmc.LOGINFO)
	#cookies = ";".join(['{0}'.format(common.quote('{0}={1}'.format(_cookie.name, _cookie.value))) for _cookie in cookie_jar])
	#final = '{0}|User-Agent={1}&Cookie={2}'.format(link, UA, cookies)
	final = '{0}|User-Agent={1}'.format(link, UA155)   # the User-Agent the ticket was requested with (GetTicket): Akamai binds its token to it
	common.PlayStream(final, quality, name, iconimage, props=dict(ResumeProps(dv), **PromptProps(playlist)), resume=resume, details=EpisodeInfos(playlist))

def GetLink(media, cdn, dv, headers, quality):
	url = ''
	media = sorted(media, key=lambda media: int(media["cdnLB"]) if media.get("cdnLB") else 0, reverse=True)
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
	if ticket is None:
		return None, None
	if url.startswith('//'):
		url = 'https:{0}'.format(url) 
	if quality == 'auto':
		return '{0}&{1}'.format(url, ticket) if '?' in url else '{0}?{1}'.format(url, ticket), None		   
	session = common.GetSession()
	# strict: a CDN that answers the playlist request with an empty body (seen for AWS on one episode, Akamai fine) is a failure, so Play tries the other one
	link = common.GetStreams('{0}&{1}'.format(url, ticket) if '?' in url else '{0}?{1}'.format(url, ticket), headers=headers, session=session, quality=quality, strict=True)
	return link, session.cookies

def GetTicket(link, headers):
	# The ticket service (mass.mako.co.il) is another origin of the same site: a browser sends the Chrome 155 set with sec-fetch-site same-site
	ticket_headers = dict(browserHeaders, **{"Origin": "https://www.mako.co.il", "Sec-Fetch-Site": "same-site"})
	result = ReadJson(link, ticket_headers)
	if result is None:
		time.sleep(2)
		result = ReadJson(link, headers)
	if not isinstance(result, dict) or 'caseId' not in result:
		xbmc.log("keshet GetTicket: no ticket answer", xbmc.LOGERROR)
		return
	if result['caseId'] == '4':
		result = Login()
		result = ReadJson(link, ticket_headers)
		if not isinstance(result, dict) or result.get('caseId') != '1':
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
	if searchText == None or searchText == '':
		return
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
		if moreData == '':
			moreData = 'auto'
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
