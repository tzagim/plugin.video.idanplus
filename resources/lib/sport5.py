# -*- coding: utf-8 -*-
import xbmc
import sys, os, re, json, time
import resources.lib.common as common

module = 'sport5'
vodUrl = 'https://vod.sport5.co.il'
radioUrl = 'https://radio.sport5.co.il'
radioIcon = 'images/photo_cover.png'
userAgent = common.GetUserAgent()
headers = {"User-Agent": userAgent}
moduleIcon = common.GetIconFullPath("Sport5.png")

def GetMainList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 6, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '', 0, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות מאתר ספורט 5"}, module=module)
	name = common.GetLabelColor("תכניות רדיו", bold=True, color="none")
	common.addDir(name, '', 20, iconimage, infos={"Title": name, "Plot": "צפיה בתכניות רדיו מאתר ספורט 5"}, module=module)

def GetCategories():
	url = '{0}/HTML/External/VodCentertDS.txt'.format(vodUrl)
	sport5File = os.path.join(common.profileDir, 'vodSport5.json')
	data = common.GetUpdatedList(sport5File, url, deltaInSec=3600, decode_text="utf-8-sig")
	#data = common.GetUpdatedList(sport5File, url, deltaInSec=3600)
	if data == []:
		common.DelFile(sport5File)
		return {}
	return data.get('Category', {}).get('Category', {})
	
def GetCategoriesList(iconimage):
	categories = GetCategories() 
	grids_arr = []
	for category in categories:
		name = common.GetLabelColor(category['Name'], keyColor="prColor", bold=True)
		grids_arr.append((name, category['ID']))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, id in grids_sorted:
		common.addDir(name, id, 1, iconimage, infos={"Title": name}, module=module)

def GetCategory(id, categories):
	if not isinstance(categories, list) and 'Category' in categories:
		categories = categories['Category']
		if not isinstance(categories, list):
			return categories
	for category in categories:
		if id == category['ID']:
			return category
	return {}
			
def GetSubCategory(id):
	url = '{0}/ajax/GetAllCategories.aspx/GettMessage?catID={1}'.format(vodUrl, id)
	data = common.OpenURL(url)
	#return json.loads(data.decode("utf-8-sig"))['Category']['Category']
	return json.loads(data)['Category']['Category']
				
def GetSeasonList(id, iconimage):
	category = GetCategories()
	ids = id.split(';')
	for i in range(len(ids)):
		category = GetCategory(ids[i], category)
	if 'Category' in category:
		catName = common.GetLabelColor(category['Name'], keyColor="prColor", bold=True)
		if not isinstance(category['Category'], list):
			name = '{0} - {1}'.format(catName, common.GetLabelColor(category['Category']['Name'], keyColor="timesColor", bold=True))
			common.addDir(name, '{0};{1}'.format(id, category['Category']['ID']), 1, iconimage, infos={"Title": name}, module=module)
		else:
			for season in category['Category']:
				name = '{0} - {1}'.format(catName, common.GetLabelColor(season['Name'], keyColor="timesColor", bold=True))
				common.addDir(name, '{0};{1}'.format(id, season['ID']), 1, iconimage, infos={"Title": name}, module=module)
	if len(ids) > 1:
		category = GetSubCategory(category['ID'])
	if 'Items' in category:
		for item in category['Items']['Item']:
			name = common.GetLabelColor(item['title'], keyColor="chColor", bold=True)
			link = item['stream_url'] if 'http' in item['stream_url'] else item['stream_url_bak']
			common.addDir(name, link, 4, item['img_upload'], infos={"Title": name, 'Plot': item['abstract']}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(item['img_upload']), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_{4}_res&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(item['img_upload']), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)

def Play(name, url, iconimage, quality='best'):
	link = referer = url
	headers['Referer'] = referer
	match = re.compile('videoUrl=(.*?)&').findall(referer)
	if len(match) > 0:
		link = match[0]
	else:
		match = re.compile('clipId=(.*?)&').findall(referer)
		if len(match) > 0:
			link = 'https://sport5-vh.akamaihd.net/i/{0}video{1}.csmil/master.m3u8'.format('UEFA/' if '/UCL2017' in referer else '', match[0])
	link = common.GetStreams(link, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}&Referer={2}'.format(link, userAgent, referer)
	common.PlayStream(final, quality, name, iconimage)

def GetRadioData(node='data'):
	headers['Referer'] = radioUrl
	sport5File = os.path.join(common.profileDir, 'sport5.json')
	result = common.GetUpdatedList(sport5File, '{0}/data/data.json?v={1}'.format(radioUrl, int(time.time() * 1000)), headers=headers, deltaInSec=3600)
	if result == []:
		common.DelFile(sport5File)
		return {}
	return result[node]

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = {
		'5live': {'ch': 'liveurl', 'link': 'https://sport5-lh.akamaihd.net/i/radio5_0@65353/master.m3u8'},
		'5studio': {'ch': 'studioUrl', 'link': 'https://sport5-lh.akamaihd.net/i/radiolivev_0@698733/index_1_av-p.m3u8'}
	}
	link = channels[url]['link']
	try:
		link = GetRadioData(channels[url]['ch'])
	except Exception as ex:
		xbmc.log(str(ex), 3)
	link1 = common.GetStreams(link, headers=headers, quality=quality)
	if link1 == link:
		link1 = channels[url]['link']
	final = '{0}|User-Agent={1}&Referer={2}'.format(link1, userAgent, radioUrl)
	common.PlayStream(final, quality, name, iconimage)

def GetRadioCategoriesList(iconimage):
	grids_arr = []
	data = GetRadioData()
	for id in data['root']['children']:
		category = data[id]
		name = common.GetLabelColor(category['name'], keyColor="timesColor", bold=True)
		grids_arr.append((name, id, '{0}/{1}'.format(radioUrl, radioIcon), {"Title": name}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, icon, infos in grids_sorted:
		common.addDir(name, link, 21, icon, infos=infos, module=module)

def GetRadioSeriesList(url):
	grids_arr = []
	data = GetRadioData()
	for id in data[url]['children']:
		serie = data[id]
		name = common.GetLabelColor(serie['name'], keyColor="prColor", bold=True)
		grids_arr.append((name, id, '{0}/{1}'.format(radioUrl, serie.get('imageUrl', radioIcon)), {"Title": name}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, icon, infos in grids_sorted:
		common.addDir(name, link, 22, icon, infos=infos, module=module)
		
def GetRadioEpisodesList(url):
	data = GetRadioData()
	for id in data[url]['children']:
		episode = data[id]
		name = common.GetLabelColor(episode['name'], keyColor="chColor")
		desc = episode.get('description', '')
		link = episode['url'].replace(u'\u200f', '')
		iconimage = '{0}/{1}'.format(radioUrl, episode['imageUrl'])
		common.addDir(name, link, 23, iconimage, infos={"Title": name, "Plot": desc, "Aired": episode['time']}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(iconimage), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_{4}_res&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(iconimage), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)

def PlayRadioEpisode(name, url, iconimage, quality='best'):
	link = common.GetStreams(url, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy, bitrate
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	
	if mode == -1:
		GetMainList(moduleIcon)
	elif mode == 0:		
		GetCategoriesList(moduleIcon)
	elif mode == 1:
		GetSeasonList(url, moduleIcon)					
	elif mode == 4:
		Play(name, url, iconimage, moreData)
	elif mode == 6:
		common.ToggleSortMethod('{0}SortBy'.format(module), sortBy)
	elif mode == 10:
		WatchLive(url, name, moduleIcon, moreData)
	elif mode == 20:
		GetRadioCategoriesList(moduleIcon)
	elif mode == 21:
		GetRadioSeriesList(url)
	elif mode == 22:
		GetRadioEpisodesList(url)
	elif mode == 23:
		PlayRadioEpisode(name, url, iconimage, moreData)
		
	common.SetViewMode('episodes')
