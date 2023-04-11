# -*- coding: utf-8 -*-
import xbmc
import sys, re
import resources.lib.common as common

module = '14tv'
moduleIcon = common.GetIconFullPath("14tv.png")
baseUrl = 'https://www.now14.co.il'

def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 4, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '', 0, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות ערוץ עכשיו 14"}, module=module)

def GetSeriesList(iconimage):
	#text = common.OpenURL(baseUrl)
	text = common.OpenURL('{0}/tochniot_haarutz/%D7%94%D7%9E%D7%94%D7%93%D7%95%D7%A8%D7%94-%D7%94%D7%9E%D7%A8%D7%9B%D7%96%D7%99%D7%AA/'.format(baseUrl))
	match = re.compile 	('<main class="content vod-content">(.*?)<!-- End Up Section -->', re.S).findall(text)
	match = re.compile('<a href="(.*?)" data-id.*?src="(.*?)".*?"tochnit_name">(.*?)</div>', re.S).findall(match[0])
	grids_arr = []
	for link, iconimage, name in match[1:]:
		iconimage = GetQuoteUrl(iconimage)
		#name = common.unquote(common.encode(link[link.rfind('/')+1:], 'utf-8'))
		name = common.GetLabelColor(common.UnEscapeXML(name.replace('-', ' ')), keyColor="prColor", bold=True)
		if iconimage.startswith('http') == False:
			iconimage = '{0}{1}'.format(baseUrl, iconimage)
		grids_arr.append((name, '{0}{1}'.format(baseUrl, link), iconimage, {"Title": name}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, image, infos in grids_sorted:
		common.addDir(name, link, 1, common.encode(image, 'utf-8'), infos=infos, module=module)

def GetQuoteUrl(url):
	b = url.rfind('/')
	e = url.rfind(".")
	n = url[b+1:e]
	url = url[:b+1] + common.quote(common.encode(n, 'utf-8')) + url[e:]
	return url

def GetEpisodesList(url, image):
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	text = common.OpenURL(url)
	#lastEpisode = re.compile('<div class=\'kaltura-zone\'>.*?src=".*?data-guid=(.*?)"></iframe>.*?<h1.*?>(.*?)</h1>.*?<div class="date-zone">.*?\((.*?)\).*?</div>', re.S).findall(text)
	#videoid = lastEpisode[0][0].strip()
	#date = lastEpisode[0][2].replace('/', '.')
	#name = common.GetLabelColor('{0} - {1}'.format(common.UnEscapeXML(lastEpisode[0][1].strip()), date), keyColor="chColor")
	#iconimage = 'https://frankly-vod.akamaized.net/channel14/transcoded/{0}/poster.jpg'.format(videoid)
	#link = 'https://frankly-vod.akamaized.net/channel14/transcoded/{0}/hls/master.m3u8'.format(videoid)
	#common.addDir(name, link, 2, iconimage, infos={"Title": name, "Aired": date}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=set_14tv_res&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(iconimage), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)
	episodes = re.compile('<div class="katan-unit(.*?)</div>\s*</div>\s*</div>', re.S).findall(text)
	for episode in episodes:
		match = re.compile('data-videoid="(.*?)".*?src=["\'](.*?)["\'].*?<div class="the-title">(.*?)</div>.*?<div class="episode_air_date"\s*?>(.*?)</div>', re.S).findall(episode)
		for videoid, iconimage, name, date in match:
			name = common.GetLabelColor('{0} - {1}'.format(common.UnEscapeXML(name.strip()), date), keyColor="chColor")
			iconimage = GetQuoteUrl(iconimage)
			if iconimage.startswith('/'):
				iconimage = '{0}{1}'.format(baseUrl, iconimage)
			link = 'https://frankly-vod.akamaized.net/channel14/transcoded/{0}/hls/master.m3u8'.format(videoid.strip())
			common.addDir(name, link, 2, iconimage, infos={"Title": name, "Aired": date}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=set_14tv_res&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(iconimage), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)

def Play(name, url, iconimage, quality='best'):
	userAgent = common.GetUserAgent()
	link = common.GetStreams(url, headers={"User-Agent": userAgent}, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Watch(name, iconimage, quality='best'):
	url = 'https://ch14-channel14.akamaized.net/hls/live/2097589/CH14_CHANNEL14/master.m3u8'
	Play(name, url, iconimage, quality)

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	
	if mode == -1:
		GetCategoriesList(moduleIcon)
	if mode == 0:		#------------- Series: ---------------
		GetSeriesList(moduleIcon)
	elif mode == 1:		#------------- Episodes: -----------------
		GetEpisodesList(url, iconimage)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
	elif mode == 3:		#--- Move to a specific episodes' page  --
		url, pages = url.split('?pages=')
		page = common.GetIndexFromUser(name, pages)
		if page > 1: 
			url = '{0}page/{1}/'.format(url, page)
		GetEpisodesList(url, iconimage)
	elif mode == 4:		#------------- Toggle Lists' sorting method -----
		common.ToggleSortMethod('14tvSortBy', sortBy)
	elif mode == 10:	#------------- Watch live channel  -------
		Watch(name, iconimage, moreData)
		
	common.SetViewMode('episodes')
