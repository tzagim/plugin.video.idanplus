# -*- coding: utf-8 -*-
import xbmc
import sys, re, json, datetime
import resources.lib.common as common
from resources.lib import cache as  cache

module = '14tv'
moduleIcon = common.GetIconFullPath("14tv.png")
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


def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 4, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '', 0, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות ערוץ עכשיו 14"}, module=module)

def GetSeriesList(iconimage):
	text = cache.get(common.OpenURL, 24, '{0}pages/66d85aaa6e9a9c00237dec06'.format(apiUrl), apiHeaders, table='pages')
	series = json.loads(text).get("sections", [{}])[0].get("items", [])
	grids_arr = []
	for serie in series:
		name = common.GetLabelColor(common.UnEscapeXML(serie["title"]), keyColor="prColor", bold=True)	
		grids_arr.append((name, '{0}pages/series/{1}'.format(apiUrl, serie["id"]), serie["image"], {"Title": name, "Plot": serie.get("description", "")}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, image, infos in grids_sorted:
		common.addDir(name, link, 5, common.encode(image, 'utf-8'), infos=infos, module=module)

def GetSeasonsList(url, image):
	text = cache.get(common.OpenURL, 24, url, apiHeaders, table='pages')
	seasons = json.loads(text).get("seasons", [])
	for season in seasons:
		name = common.GetLabelColor(season["title"], keyColor="timesColor", bold=True)
		common.addDir(name, url, 1, image, infos={"Title": name}, module=module, moreData=season["title"])

def GetEpisodesList(url, image, seasonName):
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	text = cache.get(common.OpenURL, 24, url, apiHeaders, table='pages')
	seasons = json.loads(text).get("seasons", [])
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
			common.addDir(name, episode["videoUrl"], 2, image, infos={"Title": name, "Plot": episode.get("keywords", ""), "Aired": aired}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(episode["videoUrl"]), name, common.quote_plus(image), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=2&iconimage={3}&moredata=set_14tv_res&module={4})'.format(sys.argv[0], common.quote_plus(episode["videoUrl"]), name, common.quote_plus(image), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)
		break

def Play(name, url, iconimage, quality='best'):
	link = common.GetStreams(url, headers={"referer": "https://vod.c14.co.il/", "User-Agent": userAgent}, quality=quality)
	final = '{0}|Referer=https://vod.c14.co.il/&User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Watch(name, iconimage, quality='best'):
	channels = common.GetChannelsLinks("tv", module)
	link = channels['link']
	try:
		data = common.OpenURL(channels['ch'], headers={"x-tenant-id": "channel14", "user-agent": userAgent}, responseMethod='json')
		link = data.get('vod').get('hlsMaster')
	except Exception as ex:
		xbmc.log(str(ex), 3)
	Play(name, link, iconimage, quality)

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
