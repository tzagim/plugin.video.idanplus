# -*- coding: utf-8 -*-
import sys
import json
import datetime
import resources.lib.common as common
from resources.lib import cache as cache

module = '9tv'
moduleIcon = common.GetIconFullPath("9tv.png")
baseUrl = 'https://stream.9tv.co.il'
apiUrl = 'https://insight-api-shared.univtec.com/interface/'
pageId = '686d1a07d9a706e5318b5e45'
allProgramsSectionId = '68850f7745dda4180ff2f84c'
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
apiHeaders = {
	"accept": "*/*",
	"origin": baseUrl,
	"referer": "{0}/".format(baseUrl),
	"platform": "web",
	"user-agent": userAgent,
	"x-device-type": "web",
	"x-tenant-id": "channel9",
}
skipSectionTitles = {
	'продолжить просмотр',
	'рекомендовано для вас',
	'мой список',
	'прямой эфир',
}

def ApiGet(path):
	text = cache.get(common.OpenURL, 6, '{0}{1}'.format(apiUrl, path.lstrip('/')), apiHeaders, table='pages')
	if text is None or text == '':
		return None
	if isinstance(text, (dict, list)):
		return text
	try:
		return json.loads(text)
	except Exception:
		return None

def ParseDuration(value):
	if value in (None, ''):
		return None
	if isinstance(value, (int, float)):
		return int(value)
	text = str(value).strip()
	if text.isdigit():
		return int(text)
	parts = text.split(':')
	if len(parts) == 3:
		try:
			h, m, s = [int(float(p)) for p in parts]
			return h * 3600 + m * 60 + s
		except Exception:
			return None
	if len(parts) == 2:
		try:
			m, s = [int(float(p)) for p in parts]
			return m * 60 + s
		except Exception:
			return None
	return None

def EpisodeInfos(title, plot='', aired=None, duration=None):
	infos = {"title": title, "plot": plot or ''}
	if aired:
		infos["Aired"] = aired
	seconds = ParseDuration(duration)
	if seconds is not None:
		infos["duration"] = seconds
	return infos

def FormatDate(ts):
	if ts is None:
		return None
	try:
		return datetime.datetime.fromtimestamp(ts * 0.001).strftime('%d/%m/%Y')
	except Exception:
		return None

def ItemImage(item, fallback=''):
	return item.get('image') or item.get('poster') or item.get('optimizedImage') or item.get('logo') or fallback or moduleIcon

def CleanTitle(title):
	if title is None:
		return ''
	title = common.UnEscapeXML(title).replace('.mp4', '').replace('_', ' ').strip()
	return title

def IsSeriesItem(item):
	return item.get('entity') == 'series' or item.get('type') in ('shows', 'series', 'show')

def IsPlayableItem(item):
	return bool(item.get('videoUrl')) or item.get('entity') in ('vods', 'channels') or item.get('type') in ('clips', 'vod', 'channel', 'episodes', 'episode')

def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 4, iconimage, {"title": name, "plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)

	name = common.GetLabelColor("כל התוכניות", bold=True, color="none")
	common.addDir(name, allProgramsSectionId, 0, iconimage, infos={"title": name, "plot": "צפיה בתוכניות ערוץ 9"}, module=module)

	data = ApiGet('pages/{0}'.format(pageId))
	if not data:
		return
	for section in data.get('sections') or []:
		title = (section.get('title') or section.get('name') or '').strip()
		if title == '' or title.lower() in skipSectionTitles:
			continue
		items = section.get('items') or []
		if len(items) == 0:
			continue
		sectionId = section.get('sectionId') or section.get('id') or section.get('_id')
		if not sectionId:
			continue
		if sectionId == allProgramsSectionId:
			continue
		# Prefer series folders vs playable clip lists
		if any(IsSeriesItem(it) for it in items):
			mode = 0
		else:
			mode = 6
		name = common.GetLabelColor(CleanTitle(title), bold=True, color="none")
		image = ItemImage(items[0], iconimage)
		common.addDir(name, sectionId, mode, image, infos={"title": name}, module=module)

def GetSeriesList(sectionId, iconimage):
	if sectionId in (None, '', 'None'):
		sectionId = allProgramsSectionId
	data = ApiGet('pages/section/{0}?page=1&limit=100'.format(sectionId))
	if not data:
		return
	items = data.get('items') or []
	grids_arr = []
	for serie in items:
		if not IsSeriesItem(serie):
			continue
		title = CleanTitle(serie.get('title') or serie.get('name') or '')
		if title == '' or not serie.get('id'):
			continue
		name = common.GetLabelColor(title, keyColor="prColor", bold=True)
		image = ItemImage(serie, iconimage)
		plot = serie.get('description') or ''
		grids_arr.append((name, serie['id'], image, {"title": name, "plot": plot}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr, key=lambda x: x[0])
	for name, link, image, infos in grids_sorted:
		common.addDir(name, link, 5, common.encode(image, 'utf-8') if image else iconimage, infos=infos, module=module)

def GetSeasonsList(url, image):
	data = ApiGet('pages/series/{0}'.format(url))
	if not data:
		return
	seasons = data.get('seasons') or []
	if len(seasons) <= 1:
		GetEpisodesList(url, image, 0)
		return
	for idx, season in enumerate(seasons):
		raw = season.get('title') or season.get('name') or season.get('season')
		title = CleanTitle(str(raw)) if raw not in (None, '') else "עונה {0}".format(idx + 1)
		name = common.GetLabelColor(title, keyColor="timesColor", bold=True)
		common.addDir(name, url, 1, image or ItemImage(data, moduleIcon), infos={"title": name}, module=module, moreData=str(idx))

def GetEpisodesList(url, image, seasonIndex):
	data = ApiGet('pages/series/{0}'.format(url))
	if not data:
		return
	seasons = data.get('seasons') or []
	try:
		seasonIndex = int(seasonIndex)
	except Exception:
		seasonIndex = 0
	if seasonIndex < 0 or seasonIndex >= len(seasons):
		seasonIndex = 0
	if len(seasons) == 0:
		return
	episodes = seasons[seasonIndex].get('episodes') or []
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	seriesTitle = CleanTitle(data.get('title') or '')
	for episode in episodes:
		aired = FormatDate(episode.get('date') or episode.get('airDate'))
		title = CleanTitle(episode.get('title') or '')
		name = common.GetLabelColor('{0}{1}'.format(title, ' - {0}'.format(aired) if aired else ''), keyColor="chColor")
		epImage = ItemImage(episode, image)
		videoUrl = episode.get('videoUrl') or ''
		if videoUrl == '':
			continue
		plot = episode.get('description') or seriesTitle
		common.addDir(
			name, videoUrl, 2, epImage,
			infos=EpisodeInfos(name, plot, aired, episode.get('duration')),
			contextMenu=[
				(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(videoUrl), common.quote_plus(name), common.quote_plus(epImage), module)),
				(common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=set_9tv_res&module={4})'.format(sys.argv[0], common.quote_plus(videoUrl), common.quote_plus(name), common.quote_plus(epImage), module)),
			],
			module=module, moreData=bitrate, isFolder=False, isPlayable=True
		)

def GetSectionItems(sectionId, iconimage):
	data = ApiGet('pages/section/{0}?page=1&limit=100'.format(sectionId))
	if not data:
		return
	items = data.get('items') or []
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	grids_arr = []
	for item in items:
		title = CleanTitle(item.get('title') or item.get('name') or '')
		if title == '':
			continue
		image = ItemImage(item, iconimage)
		aired = FormatDate(item.get('date') or item.get('airDate'))
		plot = item.get('description') or ''
		if IsSeriesItem(item):
			name = common.GetLabelColor(title, keyColor="prColor", bold=True)
			grids_arr.append(('series', name, item.get('id'), image, {"title": name, "plot": plot}, None))
		elif IsPlayableItem(item):
			videoUrl = item.get('videoUrl') or ''
			if videoUrl == '':
				continue
			name = common.GetLabelColor('{0}{1}'.format(title, ' - {0}'.format(aired) if aired else ''), keyColor="chColor")
			grids_arr.append(('vod', name, videoUrl, image, {"title": name, "plot": plot, "Aired": aired or ''}, bitrate))
	if sortBy != 0:
		grids_arr = sorted(grids_arr, key=lambda x: x[1])
	for kind, name, link, image, infos, more in grids_arr:
		if kind == 'series':
			common.addDir(name, link, 5, image, infos=infos, module=module)
		else:
			common.addDir(
				name, link, 2, image, infos=infos,
				contextMenu=[
					(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), common.quote_plus(name), common.quote_plus(image), module)),
					(common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=set_9tv_res&module={4})'.format(sys.argv[0], common.quote_plus(link), common.quote_plus(name), common.quote_plus(image), module)),
				],
				module=module, moreData=more or bitrate, isFolder=False, isPlayable=True
			)

def Play(name, url, iconimage, quality='best'):
	if quality in (None, ''):
		quality = 'best'
	link = common.GetStreams(url, headers={"referer": "{0}/".format(baseUrl), "User-Agent": userAgent}, quality=quality)
	final = '{0}|Referer={1}/&User-Agent={2}'.format(link, baseUrl, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)) or '0')

	if mode == -1:
		GetCategoriesList(moduleIcon if iconimage in ('', None) else iconimage)
	elif mode == 0:
		GetSeriesList(url, iconimage or moduleIcon)
	elif mode == 5:
		GetSeasonsList(url, iconimage or moduleIcon)
	elif mode == 1:
		GetEpisodesList(url, iconimage or moduleIcon, moreData if moreData != '' else 0)
	elif mode == 2:
		Play(name, url, iconimage, moreData if moreData != '' else 'best')
	elif mode == 4:
		common.ToggleSortMethod('9tvSortBy', sortBy)
	elif mode == 6:
		GetSectionItems(url, iconimage or moduleIcon)

	common.SetViewMode('episodes')
