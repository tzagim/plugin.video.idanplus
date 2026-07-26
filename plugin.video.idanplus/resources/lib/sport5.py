# -*- coding: utf-8 -*-
import xbmc
import sys, os, re, time
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
	common.addDir(name, "toggleSortingMethod", 6, iconimage, {"title": name, "plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התכניות", bold=True, color="none")
	common.addDir(name, '', 0, iconimage, infos={"title": name, "plot": "צפיה בתכניות מאתר ספורט 5"}, module=module)
	name = common.GetLabelColor("תכניות רדיו", bold=True, color="none")
	common.addDir(name, '', 20, iconimage, infos={"title": name, "plot": "צפיה בתכניות רדיו מאתר ספורט 5"}, module=module)

def GetCategories():
	url = '{0}/HTML/External/VodCentertDS.txt'.format(vodUrl)
	sport5File = os.path.join(common.profileDir, 'vodSport5.json')
	data = common.GetUpdatedList(sport5File, url, deltaInSec=3600, decode_text="utf-8-sig")
	#data = common.GetUpdatedList(sport5File, url, deltaInSec=3600)
	if data == []:
		common.DelFile(sport5File)
		return {}
	return data.get('Category', {}).get('Category', {})
	
def GetCategoryImage(category, fallback=''):
	"""Use the first available item thumbnail as the category/series image."""
	if not isinstance(category, dict):
		return fallback
	items = category.get('Items')
	if items:
		item = items.get('Item')
		if isinstance(item, dict):
			item = [item]
		if isinstance(item, list):
			for it in item:
				img = it.get('img_upload') or it.get('img')
				if img:
					return img
	sub = category.get('Category')
	if isinstance(sub, dict):
		sub = [sub]
	if isinstance(sub, list):
		for season in sub:
			img = GetCategoryImage(season, '')
			if img:
				return img
	return fallback

def GetCategoriesList(iconimage):
	categories = GetCategories() 
	grids_arr = []
	for category in categories:
		name = common.GetLabelColor(category['Name'], keyColor="prColor", bold=True)
		icon = GetCategoryImage(category, iconimage)
		grids_arr.append((name, category['ID'], icon))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, id, icon in grids_sorted:
		common.addDir(name, id, 1, icon, infos={"title": name}, module=module)

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
	data = common.OpenURL(url, responseMethod='json')
	#return json.loads(data.decode("utf-8-sig"))['Category']['Category']
	return data['Category']['Category']
				
def GetSeasonList(id, iconimage):
	category = GetCategories()
	ids = id.split(';')
	for i in range(len(ids)):
		category = GetCategory(ids[i], category)
	icon = GetCategoryImage(category, iconimage) or iconimage
	if 'Category' in category:
		catName = common.GetLabelColor(category['Name'], keyColor="prColor", bold=True)
		if not isinstance(category['Category'], list):
			name = '{0} - {1}'.format(catName, common.GetLabelColor(category['Category']['Name'], keyColor="timesColor", bold=True))
			seasonIcon = GetCategoryImage(category['Category'], icon)
			common.addDir(name, '{0};{1}'.format(id, category['Category']['ID']), 1, seasonIcon, infos={"title": name}, module=module)
		else:
			for season in category['Category']:
				name = '{0} - {1}'.format(catName, common.GetLabelColor(season['Name'], keyColor="timesColor", bold=True))
				seasonIcon = GetCategoryImage(season, icon)
				common.addDir(name, '{0};{1}'.format(id, season['ID']), 1, seasonIcon, infos={"title": name}, module=module)
	if len(ids) > 1:
		category = GetSubCategory(category['ID'])
	if 'Items' in category:
		for item in category['Items']['Item']:
			name = common.GetLabelColor(item['title'], keyColor="chColor", bold=True)
			link = item['stream_url'] if 'http' in item['stream_url'] else item['stream_url_bak']
			itemIcon = item.get('img_upload') or icon
			common.addDir(name, link, 4, itemIcon, infos={"title": name, "plot": item['abstract']}, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(itemIcon), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_{4}_res&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(itemIcon), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)

def Play(name, url, iconimage, quality='best'):
	link = referer = url
	headers['Referer'] = referer
	match = re.compile('videoUrl=(.*?)&').findall(link)
	if len(match) > 0:
		link = match[0]
	else:
		match = re.compile('clipId=(.*?)&').findall(link)
		if len(match) > 0:
			link = 'https://sport5-vh.akamaihd.net/i/{0}video{1}.csmil/master.m3u8'.format('UEFA/' if '/UCL2017' in link else '', match[0])
	match = re.compile('src=(.*?)&').findall(link)
	if len(match) > 0:
		link = match[0]
	match = re.compile('referrer=(.*?)&').findall(referer)
	if len(match) > 0:
		referer = match[0]
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

def WatchLive(channelID, name='', iconimage='', quality='best'):
	channel = common.GetChannel(channelID)
	isAdaptive = common.GetChannelAdaptive(channel)
	linkDetails = channel.get('linkDetails')
	link = linkDetails['link']
	try:
		link = GetRadioData(linkDetails['ch']).replace('https://nekot.sport5.co.il:10000?', '')
	except Exception as ex:
		xbmc.log(str(ex), xbmc.LOGERROR)
	link1 = common.GetStreams(link, headers=headers, quality=quality)
	if link1 == link:
		link1 = linkDetails['link']
	final = '{0}|User-Agent={1}&Referer={2}'.format(link1, userAgent, radioUrl)
	common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive)

def GetRadioCategoriesList(iconimage):
	grids_arr = []
	data = GetRadioData()
	for id in data['root']['children']:
		category = data[id]
		name = common.GetLabelColor(category['name'], keyColor="timesColor", bold=True)
		grids_arr.append((name, id, '{0}/{1}'.format(radioUrl, radioIcon), {"title": name}))
	grids_sorted = grids_arr if sortBy == 0 else sorted(grids_arr,key=lambda grids_arr: grids_arr[0])
	for name, link, icon, infos in grids_sorted:
		common.addDir(name, link, 21, icon, infos=infos, module=module)

def GetRadioSeriesList(url):
	series_arr = []
	episodes_arr = []
	data = GetRadioData()
	for id in data[url]['children']:
		item = data[id]
		iconimage = '{0}/{1}'.format(radioUrl, item.get('imageUrl', radioIcon))
		if (item['type'] == 'folder'):
			name = common.GetLabelColor(item['name'], keyColor="prColor", bold=True)
			series_arr.append((name, id, iconimage, {"title": name}))
		else:
			name = common.GetLabelColor(item['name'], keyColor="chColor")
			desc = item.get('description', '')
			link = item['url'].replace(u'\u200f', '')
			episodes_arr.append((name, link, iconimage, {"title": name, "plot": desc, "aired": item['time']}))
	series_sorted = series_arr if sortBy == 0 else sorted(series_arr,key=lambda series_arr: series_arr[0])
	for name, link, icon, infos in series_sorted:
		common.addDir(name, link, 21, icon, infos=infos, module=module)
	for name, link, icon, infos in episodes_arr:
		common.addDir(name, link, 23, icon, infos=infos, contextMenu=[(common.GetLocaleString(30005), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=choose&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(icon), module)), (common.GetLocaleString(30023), 'RunPlugin({0}?url={1}&name={2}&mode=4&iconimage={3}&moredata=set_{4}_res&module={4})'.format(sys.argv[0], common.quote_plus(link), name, common.quote_plus(icon), module))], module=module, moreData=bitrate, isFolder=False, isPlayable=True)
		
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
		GetSeasonList(url, iconimage if iconimage else moduleIcon)
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
	elif mode == 23:
		PlayRadioEpisode(name, url, iconimage, moreData)
		
	common.SetViewMode('episodes')
