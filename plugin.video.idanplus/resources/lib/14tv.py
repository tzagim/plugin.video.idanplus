# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import sys, re, json, datetime, hashlib
import resources.lib.common as common
from resources.lib import cache as  cache
from resources.lib import watch_store, watch_ui

module = '14tv'
moduleIcon = common.icon14tv
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
baseUrl = 'https://www.now14.co.il'
apiUrl = 'https://insight-api-shared.univtec.com/interface/' # pages/66d85aaa6e9a9c00237dec06'
apiHeaders = {
	"accept" : "*/*",
	"accept-encoding" : "gzip, deflate, br, zstd",
	"accept-language" : "en-GB,en;q=0.9",
	"dnt" : "1",
	"origin" : "https://vod.c14.co.il",
	"platform" : "web",
	"priority": "u=1, i",
	"referer" : "https://vod.c14.co.il/",
	"sec-ch-ua" : '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
	"sec-ch-ua-mobile": "?0",
	"sec-ch-ua-platform" : '"Windows"',
	"sec-fetch-dest" : "empty",
	"sec-fetch-mode" : "cors",
	"sec-fetch-site" : "cross-site",
	"sec-gpc" : "1",
	"user-agent" : userAgent,
	"x-device-type" : "web",
	"x-tenant-id" : "channel14"
}


def _14WatchKey(video_url):
	"""מפתח היסטוריית הצפייה של פרק 14 (14tv:<hash של ה-videoUrl>), עקבי בין הרשימה לניגון."""
	if not video_url:
		return ''
	return watch_store.episode_key(module, hashlib.md5(video_url.encode('utf-8')).hexdigest()[:16])


def _14AiredISO(ms):
	"""תאריך שידור כ-YYYY-MM-DD מתוך חותמת זמן במילישניות, או ''."""
	try:
		return datetime.datetime.fromtimestamp(ms * 0.001).strftime('%Y-%m-%d')
	except Exception:
		return ''


def _14RememberSeason(url, series_title, season_title, episodes):
	"""שומר את העונה שהוצגה ב-watch_store כדי שתופיע ב'המשך צפייה'. כשל כאן לעולם לא ישבור רשימה."""
	try:
		listed = []
		for index, episode in enumerate(episodes or []):
			vurl = episode.get('videoUrl')
			key = _14WatchKey(vurl)
			if not key:
				continue
			stamp = episode.get('date') if isinstance(episode.get('date'), (int, float)) else 0
			listed.append((stamp, -index, {'key': key, 'name': common.UnEscapeXML(episode.get('title') or ''),
						   'icon': episode.get('image', ''), 'number': None, 'url': vurl,
						   'aired': _14AiredISO(episode.get('date')), 'play_mode': 2}))
		# the site lists newest first; the history keeps OLDEST first, the order "next episode" follows
		listed = [item[2] for item in sorted(listed, key=lambda item: item[:2])]
		if not listed:
			return
		m = re.search(r'/series/([^/?]+)', url)
		series_key = 'now14/{0}'.format(m.group(1)) if m else 'now14/{0}'.format(series_title)
		folder = watch_store.watch_folder(common.profileDir)
		watch_store.SeasonIndex(folder).remember_season(
			'now14/{0}/{1}'.format(m.group(1) if m else series_title, season_title), series_key,
			series_title, season_title, listed, open_season=[1, url, season_title], open_series=[5, url, ''])
		meta = watch_store.EpisodeMeta(folder)
		for episode in episodes or []:
			key = _14WatchKey(episode.get('videoUrl'))
			if not key:
				continue
			meta.remember(key, plot=common.UnEscapeXML(episode.get('keywords') or ''), aired=_14AiredISO(episode.get('date')))
	except Exception as ex:
		xbmc.log('14tv RememberSeason: {0}'.format(ex), xbmc.LOGERROR)


def _14EpisodeDetails(key):
	"""מידע וידאו של הפרק המתנגן מהעונה השמורה (ללא בקשת רשת)."""
	try:
		folder = watch_store.watch_folder(common.profileDir)
		entry = watch_store.episode_entry(watch_store.SeasonIndex(folder).load(), key)
		if entry is None:
			return {}
		facts = watch_store.EpisodeMeta(folder).load().get(key) or {}
		details = {'mediatype': 'episode'}
		if entry.get('series_title'):
			details['tvshowtitle'] = entry['series_title']
		if facts.get('plot'):
			details['plot'] = facts['plot']
		if facts.get('aired'):
			details['aired'] = facts['aired']
		return details
	except Exception:
		return {}


def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 4, iconimage, {"title": name, "plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '', 0, iconimage, infos={"title": name, "plot": "צפיה בתכניות ערוץ עכשיו 14"}, module=module)

def GetSeriesList(iconimage):
	text = cache.get(common.OpenURL, 24, '{0}pages/66d85aaa6e9a9c00237dec06'.format(apiUrl), apiHeaders, table='pages')
	series = json.loads(text).get("sections", [{}])[0].get("items", [])
	grids_arr = []
	for serie in series:
		name = common.GetLabelColor(common.UnEscapeXML(serie["title"]), keyColor="prColor", bold=True)	
		grids_arr.append((name, '{0}pages/series/{1}'.format(apiUrl, serie["id"]), serie["image"], {"title": name, "plot": serie.get("description", "")}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, image, infos in grids_sorted:
		common.addDir(name, link, 5, common.encode(image, 'utf-8'), infos=infos, module=module)

def GetSeasonsList(url, image):
	text = cache.get(common.OpenURL, 24, url, apiHeaders, table='pages')
	seasons = json.loads(text).get("seasons", [])
	for season in seasons:
		name = common.GetLabelColor(season["title"], keyColor="timesColor", bold=True)
		common.addDir(name, url, 1, image, infos={"title": name}, module=module, moreData=season["title"])

def GetEpisodesList(url, image, seasonName):
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	text = cache.get(common.OpenURL, 24, url, apiHeaders, table='pages')
	data = json.loads(text)
	seriesTitle = data.get("title", "")
	seasons = data.get("seasons", [])
	for season in seasons:
		if season["title"] != seasonName:
			continue
		episodes = season.get("episodes", [])
		for episode in episodes:
			aired = episode.get("date")
			if aired != None:
				aired = datetime.datetime.fromtimestamp(aired*0.001).strftime('%d/%m/%Y')
			name = common.GetLabelColor('{0}{1}'.format(episode["title"], ' - {0}'.format(aired) if aired != None else ""), keyColor="chColor")
			image = episode["image"]
			common.addDir(name, episode["videoUrl"], 2, image, infos={"title": name, "plot": episode.get("keywords", ""), "Aired": aired}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(episode["videoUrl"]), name, common.quote_plus(image), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=set_14tv_res&module={4})'.format(sys.argv[0], common.quote_plus(episode["videoUrl"]), name, common.quote_plus(image), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)
		_14RememberSeason(url, seriesTitle, seasonName, episodes)
		break

def Play(name, url, iconimage, quality='best', isAdaptive=False, key=''):
	resume = None
	if key:
		proceed, resume = watch_ui.ChooseResume(key, name, iconimage)
		if not proceed:
			if common.GetHandle() >= 0:   # run as a script (handle -1) nothing waits for an answer: cancelling is quiet
				xbmcplugin.setResolvedUrl(common.GetHandle(), False, xbmcgui.ListItem())
			return
	link = common.GetStreams(url, headers={"referer": "https://vod.c14.co.il/", "User-Agent": userAgent}, quality=quality)
	final = '{0}|Referer=https://vod.c14.co.il/&User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive,
					  props={'idanplus_key': key} if key else None, resume=resume,
					  details=_14EpisodeDetails(key) if key else None)

def Watch(channelID, name, iconimage, quality='best'):
	channel = common.GetChannel(channelID)
	isAdaptive = common.GetChannelAdaptive(channel)
	linkDetails = channel.get('linkDetails')
	link = linkDetails['link']
	try:
		data = common.OpenURL(linkDetails['ch'], headers={"x-tenant-id": "channel14", "user-agent": userAgent}, responseMethod='json')
		link = data.get('vod').get('hlsStream')
	except Exception as ex:
		xbmc.log(str(ex), xbmc.LOGERROR)
	Play(name, link, iconimage, quality, isAdaptive=isAdaptive)

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	
	if mode == -1:
		GetCategoriesList(moduleIcon)
	if mode == 0:		#------------- Series: ---------------
		GetSeriesList(moduleIcon)
	elif mode == 5:		#------------- Seasons: -----------------
		GetSeasonsList(url, iconimage)
	elif mode == 1:		#------------- Episodes: -----------------
		GetEpisodesList(url, iconimage, moreData)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData, key=_14WatchKey(url))
	elif mode == 3:		#--- Move to a specific episodes' page  --
		url, pages = url.split('?pages=')
		page = common.GetIndexFromUser(name, pages)
		if page > 1: 
			url = '{0}page/{1}/'.format(url, page)
		GetEpisodesList(url, iconimage)
	elif mode == 4:		#------------- Toggle Lists' sorting method -----
		common.ToggleSortMethod('14tvSortBy', sortBy)
	elif mode == 10:	#------------- Watch live channel  -------
		Watch(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')
