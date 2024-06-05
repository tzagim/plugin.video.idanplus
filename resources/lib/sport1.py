# -*- coding: utf-8 -*-
import xbmc
import sys, re
import resources.lib.common as common

module = 'sport1'
baseUrl = 'https://sport1.maariv.co.il'
moduleIcon = common.GetIconFullPath("sport1.jpg")

def GetMainList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 6, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '', 0, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות מאתר ספורט 1"}, module=module)

def GetCategoriesList(iconimage):
	url = '{0}/vod/'.format(baseUrl)
	text = common.OpenURL(url)
	matches = re.compile(u'<div class="vod-slider">(.*?)<div class="tab-content">', re.S).findall(text)
	grids_arr = []
	for match in matches:
		category = re.compile(u'<h2.*?>(.*?)</h2>.*?<a.*?href="(.*?)"', re.S).findall(match)
		if len(category) < 1:
			continue
		name, link = category[0]
		name = common.GetLabelColor(name.strip(), keyColor="prColor", bold=True)
		grids_arr.append((name, link))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link in grids_sorted:
		common.addDir(name, '{0}/vod/{1}'.format(baseUrl, link), 1, iconimage, infos={"Title": name}, module=module)

def GetEpisodes(text):
	#raw_unicode_escape = False
	#match = []#re.compile(u'<main id="main"(.*?)</main>', re.S).findall(text)
	#if len(match) < 1:
	match = re.compile(u'pageGlobals.*?"id":(.*?),').findall(text)
	link = 'https://sport1.maariv.co.il/wp-json/sport1/v1/league/{0}/video/content?is_mobile=false&rows=800'.format(match[0])
	text = common.OpenURL(link)
	match[0] = text.replace('\\"', '"').replace('\/', '/')
	#raw_unicode_escape = True
	match = re.compile(u'<div class="video-card(.*?)</a>', re.S).findall(match[0])
	for item in match:
		m = re.compile("<a href=['\"](.*?)['\"].*?<img(.*?)>.*?<h3.*?>(.*?)</h3>", re.S).findall(item)
		if len(m) < 1:
			continue
		url, icon, name = m[0]
		m = re.compile(u'data-lazy="(.*?)"', re.S).findall(icon)
		if len(m) < 1:
			m = re.compile(u'src=["\'](.*?)["\']', re.S).findall(icon)
		icon = m[0]
		#if raw_unicode_escape:
		name = common.decode(name, 'raw_unicode_escape', force=True)
		url = common.decode(url, 'raw_unicode_escape', force=True)
		icon = common.decode(icon, 'raw_unicode_escape', force=True)
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="chColor", bold=True)
		try:
			common.addDir(name, url.replace(baseUrl, ''), 4, icon, infos={"Title": name}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(url), name, common.quote_plus(icon), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_{4}_res&module={4})'.format(sys.argv[0], common.quote_plus(url), name, common.quote_plus(icon), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)
		except Exception as ex:
			xbmc.log(str(ex), 3)
			
def GetEpisodesList(url, iconimage):
	text = common.OpenURL(url)
	GetEpisodes(text)

def Play(url, name='', iconimage='', quality='best'):
	try:
		userAgent = common.GetUserAgent()
		result = common.OpenURL('{0}{1}'.format(baseUrl, url), headers={"User-Agent": userAgent})
		id = re.compile(u'id="walla-iframe-video".*?src=".*?media=(.*?)&', re.S).findall(result)[0]
		result = common.OpenURL('https://dal.walla.co.il/media/{0}?origin=www.walla.co.il'.format(id), headers={}, responseMethod='json')
		if result is None or result.get("result", "") != "success":
			return
		video = result.get("data", {}).get("video", {})
		if video == {}:
			return
		if len(video.get("stream_urls", [])) > 0:
			link = video["stream_urls"][-1]["stream_url"]
		else:
			if video.get("url", "") != "":
				link = video["url"]
				link = common.GetStreams(link, headers={"User-Agent": userAgent}, quality=quality)
			else:
				return
		final = '{0}|User-Agent={1}'.format(link, userAgent)
		common.PlayStream(final, quality, name, iconimage)
	except Exception as ex:
		xbmc.log(str(ex), 3)

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy, bitrate
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	
	if mode == -1:
		GetMainList(moduleIcon)
	elif mode == 0:		
		GetCategoriesList(moduleIcon)
	elif mode == 1:
		GetEpisodesList(url, moduleIcon)					
	elif mode == 4:
		Play(url, name, iconimage, moreData)
	elif mode == 6:
		common.ToggleSortMethod('{0}SortBy'.format(module), sortBy)
		
	common.SetViewMode('episodes')
