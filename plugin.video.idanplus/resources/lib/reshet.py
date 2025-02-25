# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import sys, re, json, collections, datetime, time
import resources.lib.common as common
from resources.lib import cache as  cache

Addon = xbmcaddon.Addon(common.AddonID)
module = 'reshet'

baseUrl = 'https://13tv.co.il'
userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36"
brvApi = 'https://edge.api.brightcove.com/playback/v1/accounts/1551111274001/videos/'
brvPk = 'application/json;pk=BCpkADawqM30eqkItS5d08jYUtMkbTKu99oEBllbfUaFKeknXu4iYsh75cRm2huJ_b1-pXEPuvItI-733TqJN1zENi-DcHlt7b4Dv6gCT8T3BS-ampD0XMnORQLoLvjvxD14AseHxvk0esW3'
cstApi = 'https://13tv-api.oplayer.io/api/getlink'
cstUserId = '45E4A9FB-FCE8-88BF-93CC-3650C39DDF28'
moduleIcon = common.GetIconFullPath("13.jpg")

def GetCategoriesList(iconimage):
	name = "{0}: {1}".format(common.GetLocaleString(30001), common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003))
	common.addDir(name, "toggleSortingMethod", 5, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '{0}/all-shows/all-shows-list/'.format(baseUrl), 0, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות רשת 13"}, module=module)
	name = common.GetLabelColor("חדשות 13", bold=True, color="none")
	common.addDir(name, '', 10, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות חדשות 13"}, module=module)
	name = common.GetLabelColor("ארכיון רשת 13", bold=True, color="none")
	common.addDir(name, '{0}/general/programs/'.format(baseUrl), 20, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות מארכיון רשת 13"}, module=module)

def GetUrlJson(url, root=False):
	result = {}
	try:
		html = common.OpenURL(url, headers={'User-Agent': userAgent, 'Accept-encoding': 'gzip, deflate, br'})
		props = re.compile('"application/json">(.*?)</script>').findall(html)
		if len(props) == 0:
			return {}
		result = json.loads(props[0])
		if root == False:
			result = result['props']['pageProps']['page']
		#xbmc.log(str(result), 5)
	except Exception as ex:
		xbmc.log(str(ex), 3)
	return result

def GetSeriesListOld(url, iconimage):
	#result = GetUrlJson(url)
	result = cache.get(GetUrlJson, 24, url, table='pages')
	if result==[]:
		result = cache.get(GetUrlJson,0, url, table='pages')
	if len(result) < 1:
		return
	grids_arr = []
	seriesIDs = []
	series = {}
	grids = result.get('Content', {}).get('PageGrid', {})
	for grid in grids:
		for serie in grid.get('posts', {}):
			try:
				seriesID = serie.get('id')
				if seriesID in seriesIDs or seriesID == 170768:
					continue
				link = serie.get('link')
				'''
				postType = serie.get('postType', '')
				if postType == 'item':
					if '/movies/' in link:
						link = link[:link.find('/movies/') + 8].replace('/item', '')
					else:
						link = link[:link.find('/season') + 1].replace('/item', '')
					name = common.encode(serie['title'], 'utf-8')
					name = name[:name.find(',')]
				elif postType != 'page':
					continue
				else:
					if len(common.url_parse(link).path.split('/')) > 4 and 'channel2-news' not in link:
						continue
				'''
				video = serie.get('video')
				if video is not None:
					continue
					if '/movies/' in link:
						link = link[:link.find('/movies/') + 8].replace('/item', '')
					else:
						link = link[:link.find('/season') + 1].replace('/item', '')
				name = common.encode(serie['title'], 'utf-8')
				name = common.GetLabelColor(name, keyColor="prColor", bold=True)
				if link == '' or '/all-shows-' in link or link in series:
					continue
				series[link] = name
				seriesIDs.append(seriesID)
				image = serie['imageObj']['d']
				pageTitle = serie.get('secondaryTitle', {})
				description = '' if pageTitle is None else common.encode(pageTitle, 'utf-8')
				matches = [grids_arr.index(x) for x in grids_arr if link == x[1]]
				if len(matches) == 1:
					grids_arr[matches[0]] = (name, link, image, {"Title": name, "Plot": description,'mediatype': 'movie'})
				else:
					grids_arr.append((name, link, image, {"Title": name, "Plot": description,'mediatype': 'movie'}))
			except Exception as ex:
				xbmc.log('SerieID: {0}\n{1}'.format(seriesID, str(ex)), 3)
	mainMenus = result.get('Header', {}).get('mainMenu', [])
	for mainMenu in mainMenus:
		if mainMenu['url'] == '/vod/':
			grids = mainMenu['children']
			for grid in grids:
				name = common.GetLabelColor(common.UnEscapeXML(common.encode(grid['title'], 'utf-8')), keyColor="prColor", bold=True)
				link = grid['url']
				if link == '' or link in series or link == '/vod/' or link == '/general/programs/signup-auditions/':
					continue
				series[link] = name
				grids_arr.append((name, link, iconimage, {"Title": name}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, icon, infos in grids_sorted:
		common.addDir(name, '{0}{1}'.format(baseUrl, link), 21, str(icon), infos=infos, module=module)

def GetSeasonListOld(url, iconimage):
	#result = GetUrlJson(url)
	result = cache.get(GetUrlJson, 24, url, table='pages')
	seasons, episodes = GetLinks(url, result, iconimage)
	if len(seasons) > 0:
		for link, title in common.items(seasons):
			name = common.GetLabelColor(title, keyColor="timesColor", bold=True)
			common.addDir(name, link, 21, iconimage, infos={"Title": name}, module=module)
		if len(episodes) < 1:
			return
	ShowEpisodes(episodes, iconimage)
	ShowPaging(result, iconimage)

def GetEpisodesListOld(url, iconimage):
	#result = GetUrlJson(url)
	result = cache.get(GetUrlJson, 24, url, table='pages')
	if result==[]:
		result = cache.get(GetUrlJson, 0, url, table='pages')
	seasons, episodes = GetLinks(url, result, iconimage)
	ShowEpisodes(episodes, iconimage)
	ShowPaging(result, iconimage)

def IsLinkNotExist(url, link, seasons):
	if url[-1] == '/':
		url = url[:len(url)-1]
	if link[-1] == '/':
		link1 = link[:len(link)-1]
	return url != link and url != link1 and url in link and link.replace('episodes/', '') not in seasons and (link not in seasons or seasons[link] == '')

def GetTitleAndLink(element, t, l):
	title = '' if element is None else common.encode(element.get(t, '').strip(), 'utf-8')
	link = '' if element is None else element.get(l, '')
	link = '' if link is None else common.encode(str(link).strip(), 'utf-8')
	if len(link) > 0:
		if link[-1] != '/':
			link += '/'
		link = '{0}{1}'.format(baseUrl, link)
	return title, link

def GetSeasons(url, pageTitle, seasons, gridTitle, gridLink):
	#xbmc.log('-- {0} - {1} --'.format(gridLink, gridTitle), 5)
	if len(gridLink) > 0 and gridLink[-1] != '/':
		gridLink += '/'
	ending = gridLink[gridLink.rfind('/', 0, len(gridLink)-1):]
	if ('episodes' in ending or 'season' in ending) and IsLinkNotExist(url, gridLink, seasons):
	#	xbmc.log('-- {0} - {1} --'.format(ending, gridTitle), 5)
	#if 'episodes' in gridLink and IsLinkNotExist(url, gridLink, seasons):
		#gridLink = GetLink(gridLink)
		seasons[gridLink] = gridTitle if gridTitle != '' else pageTitle
	elif gridLink != '' and gridTitle != '' and IsLinkNotExist(url, gridLink, seasons):
		gridLink = gridLink.replace('/episodes/', '')
		seasons[gridLink] = gridTitle
	#xbmc.log(str(len(seasons)), 5)
	return seasons

def GetEpisodes(posts, episodes, gridTitle, iconimage):
	for post in posts:
		try:
			video = post.get('video')
			if video is None:
				continue
			videoID = ''
			if video.get('kalturaId') is not None:
				videoID = '{0}--kaltura--{1}==='.format(videoID, video['kalturaId'])
			if video.get('cst_videoID') is not None:
				if video['cst_videoID'] == '-1':
					videoID = '{0}--cst--{1}==='.format(videoID, video['cst_videoID'])
				else:
					videoID = '{0}--cst--{1}==='.format(videoID, video.get('videoRef', videoID))
			if video.get('brv_videoID') is not None:
				videoID = '{0}--brv--{1}==='.format(videoID, video['brv_videoID'])	
			if videoID == '':
				continue
			icon = post.get('image', iconimage)
			title = post.get('title')
			if title == None:
				title = ''
			secondaryTitle = post.get('secondaryTitle')
			if secondaryTitle == None:
				secondaryTitle = ''
			episodes.append((gridTitle, videoID, icon, common.encode(title.strip(), 'utf-8'), common.encode(secondaryTitle.strip(), 'utf-8'), post.get('publishDate')))
		except Exception as ex:
			xbmc.log(str(ex), 3)
	return episodes

def GetLinks(url, result, iconimage):
	seasons = collections.OrderedDict() if common.NewerThanPyVer('2.6.99') else {}
	episodes = []
	#'''
	subMenus = result.get('Header', {}).get('subMenu', {})
	if subMenus:
		for subMenu in subMenus:
			try:
				title = subMenu.get('title')
				link = subMenu.get('link')
				if len(link) > 0 and link[-1] != '/':
					link += '/'
				ending = link[link.rfind('/', 0, len(link)-1):]
				link = '{0}{1}'.format(baseUrl, link)
				#xbmc.log('{0} - {1}'.format(link, title), 5)
				if ('episodes' in ending or 'season' in ending) and IsLinkNotExist(url, link, seasons):
				#if IsLinkNotExist(url, link, seasons):
					#link = GetLink(link)
					#xbmc.log('added', 5)
					seasons[link] = common.encode(title.strip(), 'utf-8')
					#xbmc.log('!! {0} - {1} !!'.format(link, seasons[link]), 5)
			except Exception as ex:
				xbmc.log(str(ex), 3)
	#'''
	xbmc.log(str(seasons), 5)
	pageTitle = common.encode(result.get('PageMeta', {}).get('title', '').strip(), 'utf-8')
	for grid in result.get('Content', {}).get('PageGrid', {}):
		if grid["grid_type"] == "seven_with_banner_or_iframe":
			continue
		gridTitle, gridLink = GetTitleAndLink(grid.get('grid_title'), 'text', 'link')
		posts = grid.get('posts', [])
		if posts != []:
			#title, link = GetTitleAndLink(grid.get('grid_title'), 'text', 'link')
			#seasons = GetSeasons(url, pageTitle, seasons, title, link)
			#episodes = GetEpisodes(posts, episodes, title, iconimage)
			if gridLink != '':
				seasons = GetSeasons(url, pageTitle, seasons, gridTitle, gridLink)
			else:
				for post in posts:
					title, link = GetTitleAndLink(post, 'title', 'link')
					seasons = GetSeasons(url, pageTitle, seasons, title, link)
			episodes = GetEpisodes(posts, episodes, gridTitle, iconimage)
		else:
			elements = grid.get('matrix_elements', {})
			if elements != {}:
				for element in elements:
					title, link = GetTitleAndLink(element.get('matrix_title'), 'text', 'link')
					if link != '':
						seasons = GetSeasons(url, pageTitle, seasons, title, link)
					else:
						posts = element.get('posts', [])
						for post in posts:
							title, link = GetTitleAndLink(post, 'title', 'link')
							seasons = GetSeasons(url, pageTitle, seasons, title, link)
							episodes = GetEpisodes(posts, episodes, title, iconimage)
			else:
				gridLink = grid.get('link')
				if gridLink is not None and 'episodes' in gridLink and IsLinkNotExist(url, gridLink, seasons):
					seasons[gridLink] = common.encode(grid.get('imageObj', {}).get('alt_d', '').strip(), 'utf-8')
	return seasons, episodes

def ShowEpisodes(episodes, iconimage):
	if len(episodes) < 1:
		name = 'אין פרקים מלאים'
		common.addDir(name, '', 99, iconimage, infos={"Title": name}, module=module, isFolder=False)
		return
	for gridTitle, link, icon, title, subtitle, publishDate in episodes:
		name = common.GetLabelColor(title, keyColor="chColor") if gridTitle is None or gridTitle == '' else common.getDisplayName(gridTitle, title, programNameFormat)
		link = str(link)
		common.addDir(name, link, 3, icon, infos={"Title": name, "Plot": subtitle, "Aired": publishDate}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=3&iconimage={3}&moredata=choose&module=reshet)'.format(sys.argv[0], common.quote_plus(link), common.quote_plus(name), common.quote_plus(icon))), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=3&iconimage={3}&moredata=set_reshet_res&module=reshet)'.format(sys.argv[0], common.quote_plus(link), common.quote_plus(name), common.quote_plus(icon)))], moreData=bitrate, module=module, isFolder=False, isPlayable=True)

def ShowPaging(result, iconimage):
	grids = result.get('Content', {}).get('PageGrid', {})
	if len(grids) < 1:
		return
	paginationGrid = grids[-1]
	grid_type = paginationGrid.get('grid_type')
	if grid_type is None or grid_type != 'PaginationArray':
		return  
	else: 
		current_page = paginationGrid.get('current_page', 1)
	#if current_page > 0:
	page_url = '{0}{1}'.format(baseUrl, paginationGrid.get('base'))
	page_url = page_url[:page_url.find('%')]
	max_page = paginationGrid.get('max_page', 1)
	if current_page > 1:
		#prev_page = page_url + str(current_page-1) + '/' if current_page - 1 > 1 else page_url
		common.addDir(common.GetLabelColor(common.GetLocaleString(30011), color="green"), page_url + str(current_page-1) + '/', 22, iconimage, module=module)
	if max_page > current_page:
		common.addDir(common.GetLabelColor(common.GetLocaleString(30012), color="green"), page_url + str(current_page+1) + '/', 22, iconimage, module=module)
	if max_page > 2:
		name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
		common.addDir(name, '{0}?p={1}&pages={2}'.format(page_url, current_page, max_page), 7, iconimage, infos={"Title": name, "Plot": name}, module=module)

def Play(video, name='', iconimage='', quality='best'):
	try:
		videos = video.split('===')
		kaltura = ''
		cst = ''
		brv = ''
		for vid in videos:
			if '--kaltura--' in vid:
				kaltura = vid.replace('--kaltura--', '')
			elif '--cst--' in vid:
				cst = vid.replace('--cst--', '')
			elif '--brv--' in vid:
				brv = vid.replace('--brv--', '')
		if kaltura != '':
			link = common.GetKaltura(kaltura, 2748741, baseUrl, userAgent, quality=quality)
		elif cst != '':
			headers={"User-Agent": userAgent}
			if common.isnumeric(cst):
				result = common.OpenURL('{0}/getVideoById?userId={1}&serverType=web&videoId={2}&callback=x'.format(cstApi, cstUserId, cst), headers=headers)
			else:
				result = common.OpenURL('{0}/getlink/getVideoByFileName?userId={1}&videoName={2}&serverType=web&callback=x'.format(cstApi, cstUserId, cst), headers=headers)
			if result is not None:
				source = json.loads(result)[0]
				link = '{0}{1}{2}{3}{4}.mp4{5}{6}'.format(source['ProtocolType'], source['ServerAddress'], source['MediaRoot'], source['MediaFile'][:source['MediaFile'].find('.mp4')], source['Bitrates'], source['StreamingType'], source['Token'])
				#xbmc.log(link, 5)
				session = common.GetSession()
				link = common.GetStreams(link, headers=headers, session=session, quality=quality)
				final = '{0}|User-Agent={1}'.format(link, userAgent)
				cookies = "&".join(['Cookie={0}'.format(common.quote('{0}={1}'.format(_cookie.name, _cookie.value))) for _cookie in session.cookies])
				if cookies != '':
					final = '{0}&{1}'.format(final, cookies)
			else:
				result = common.OpenURL('{0}{1}'.format(brvApi, brv), headers={"Accept": brvPk, "User-Agent": userAgent})
				if result is None:
					link = 'https://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId={0}'.format(brv)
					link = common.GetStreams(link, headers=headers, quality=quality)
				else:
					sources = json.loads(result)['sources']
					link = ''
					avg_bitrate = 0
					for source in sources:
						if 'src' in source:
							if source['container'] == 'M2TS':
								link = common.GetStreams(source['src'], headers=headers, quality=quality)
								break
							if source['avg_bitrate'] > avg_bitrate:
								link = source['src']
								avg_bitrate = source['avg_bitrate']
								#xbmc.log('[{0}]  {1}'.format(avg_bitrate, link), 5)
				final = '{0}|User-Agent={1}'.format(link, userAgent)
		
		final = '{0}|User-Agent={1}'.format(link, userAgent)
		common.PlayStream(final, quality, name, iconimage)
	except Exception as ex:
		xbmc.log(str(ex), 3)

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("tv", module)
	referer = channels[url].get('referer')
	try:
		headers={"User-Agent": userAgent}
		if referer:
			headers['referer'] = referer
		link = common.GetStreams(channels[url]['link'], headers=headers, quality=quality)
	except Exception as ex:
		xbmc.log(str(ex), 3)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	if referer:
		final = '{0}&Referer={1}'.format(final, referer)
	common.PlayStream(final, quality, name, iconimage)

def GetNewsCategoriesList(iconimage):
	url = '{0}/news/13-programs/'.format(baseUrl)
	result = GetUrlJson(url)
	if len(result) < 1:
		return
	grids_arr = []
	grids = result.get('Content', {}).get('PageGrid', {})
	for grid in grids:
		gridType = grid.get('grid_type')
		if gridType is None:
			continue
		gridTitle = grid.get('grid_title')
		title = '' if gridTitle is None else common.GetLabelColor(common.UnEscapeXML(common.encode(gridTitle.get('text', '').strip(), 'utf-8')), keyColor="prColor", bold=True)
		link = '' if gridTitle is None else '{0}{1}'.format(baseUrl, gridTitle.get('link', ''))
		posts = grid.get('posts')
		image = iconimage if posts is None or len(posts) < 1 else posts[0].get('image', '')
		grids_arr.append((title, link, image, {"Title": title}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, icon, infos in grids_sorted:
		common.addDir(name, link, 21, icon, infos=infos, module=module)

def GetSeriesList(url, iconimage):
	#result = GetUrlJson(url, root=True)
	root = True
	result = cache.get(GetUrlJson, 72, url, root, table='pages')
	if result==[]:
		result = cache.get(GetUrlJson, 0, url, root, table='pages')
	if len(result) < 1:
		return
	result = result['props']['pageProps']['page']
	grids_arr = []
	grids = result.get('Content', {}).get('PageGrid', {})
	for grid in grids:
		for serie in grid.get('shows', {}):
			try:
				if serie['url'] == "":
					if serie['id'] == '613':
						serie['url'] = '/all-shows/vort/'
					elif serie['id'] == '655':
						serie['url'] = '/shows/patrick/'
					else:
						continue
				name = common.encode(serie['title'], 'utf-8')
				name = common.GetLabelColor(name, keyColor="prColor", bold=True)
				grids_arr.append((name, serie['url'], serie['poster'], {"Title": name, "Plot": name,'mediatype': 'movie'}))
			except Exception as ex:
				xbmc.log('SerieID: {0}\n{1}'.format(serie['id'], str(ex)), 3)
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, icon, infos in grids_sorted:
		common.addDir(name, '{0}{1}'.format(baseUrl, link), 1, str(icon), infos=infos, module=module)

def GetSeasonList(url, iconimage):
	if len(url) > 0 and url[-1] != '/':
		url += '/'
	serie = url[url.rfind('/', 0, len(url)-1)+1:-1]
	buildId = common.GetAddonSetting("reshetSiteBuildID")
	url = "{0}/_next/data/{1}/he/all-shows/{2}.json?all=all-shows&all={2}".format(baseUrl, buildId, serie)
	result = common.OpenURL(url, headers={"User-Agent": userAgent}, responseMethod='json')
	if result is None:
		result = GetUrlJson('{0}/all-shows/all-shows-list/'.format(baseUrl), root=True)
		buildId = result['buildId']
		common.SetAddonSetting("reshetSiteBuildID", buildId)
		url = "{0}/_next/data/{1}/he/all-shows/{2}.json?all=all-shows&all={2}".format(baseUrl, buildId, serie)
		result = common.OpenURL(url, headers={"User-Agent": userAgent}, responseMethod='json')
	
	grids = result['pageProps']['page']['Content']['PageGrid']
	grids_arr = []
	for grid in grids:
		if grid["grid_type"] == "VodPlaylist":
			if type(grid["episodesSeasonsMap"]) is dict:
				for key, season in common.items(grid["episodesSeasonsMap"]):
					name = common.GetLabelColor(season["name"], keyColor="timesColor", bold=True)
					grids_arr.append((key, name, url, iconimage, {"Title": name, "Plot": name}))
			else:
				for season in grid["episodesSeasonsMap"]:
					name = common.GetLabelColor(season["name"], keyColor="timesColor", bold=True)
					grids_arr.append(("0", name, url, iconimage, {"Title": name, "Plot": name}))
	grids_sorted = sorted(grids_arr,key=lambda grids_arr: grids_arr[1], reverse=True)
	for key, name, link, icon, infos in grids_sorted:
		common.addDir(name, link, 2, icon, infos={"Title": name}, moreData=key, module=module)

def GetEpisodesList(url, iconimage, seasonNum):
	result = common.OpenURL(url, headers={"User-Agent": userAgent}, responseMethod='json')
	grids = result['pageProps']['page']['Content']['PageGrid']
	grids_arr = []
	for grid in grids:
		if grid["grid_type"] == "VodPlaylist":
			season = grid["episodesSeasonsMap"][seasonNum] if type(grid["episodesSeasonsMap"]) is dict else grid["episodesSeasonsMap"][0]
			for episode in season["episodes"]:
				name = common.GetLabelColor(episode["title"], keyColor="chColor")
				link = '--kaltura--{0}==='.format(episode["video"]['kalturaId'])
				icon = episode["video"]["poster"]
				air_date = ''
				frmt = "%d/%m/%Y"
				try:
					air_date = datetime.datetime.strptime(episode["air_date"], frmt)
				except TypeError:
					air_date = datetime.datetime(*(time.strptime(episode["air_date"], frmt)[0:6]))
				grids_arr.append((air_date, name, link, icon, {"Title": name, "Plot": episode["secondaryTitle"], "Aired": episode["air_date"]}))
	grids_sorted = sorted(grids_arr,key=lambda grids_arr: grids_arr[0], reverse=True)
	for air_date, name, link, icon, infos in grids_sorted:
		common.addDir(name, link, 3, icon, infos=infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=3&iconimage={3}&moredata=choose&module=reshet)'.format(sys.argv[0], common.quote_plus(link), common.quote_plus(name), common.quote_plus(icon))), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=3&iconimage={3}&moredata=set_reshet_res&module=reshet)'.format(sys.argv[0], common.quote_plus(link), common.quote_plus(name), common.quote_plus(icon)))], moreData=bitrate, module=module, isFolder=False, isPlayable=True)

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy, bitrate, programNameFormat
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	programNameFormat = int(common.GetAddonSetting("programNameFormat"))
	
	if mode == -1:
		GetCategoriesList(moduleIcon)
	elif mode == 0:
		GetSeriesList(url, moduleIcon)					# Series
	elif mode == 1:
		GetSeasonList(url, iconimage)					# Seasons
	elif mode == 2:
		GetEpisodesList(url, iconimage, moreData)		# Episodes
	elif mode == 3:
		Play(url, name, iconimage, moreData)			# Playing episode
	elif mode == 4:
		WatchLive(url, name, iconimage, moreData)		# Playing Live
	elif mode == 5:	
		common.ToggleSortMethod('reshetSortBy', sortBy)	# Toggle Lists' sorting method
	#elif mode == 6:
	#	GetGridList(moduleIcon, url)
	elif mode == 7:										#--- Move to a specific episodes' page  --
		urlp = common.url_parse(url)
		prms = common.parse_qs(urlp.query)
		page = common.GetIndexFromUser(name, int(prms['pages'][0]))
		if page == 0:
			page = int(prms['p'][0])
		url = '{0}{1}{2}/'.format(baseUrl, urlp.path, page)
		GetEpisodesListOld(url, iconimage)
	elif mode == 10:
		GetNewsCategoriesList(moduleIcon)				# News Shows
	elif mode == 20:
		GetSeriesListOld(url, moduleIcon)				# Series
	elif mode == 21:
		GetSeasonListOld(url, iconimage)				# Seasons
	elif mode == 22:
		GetEpisodesListOld(url, iconimage)				# Episodes
	
	if mode != 0 and mode != 1:
		common.SetViewMode('episodes')
