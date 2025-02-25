# -*- coding: utf-8 -*-
import xbmc
import resources.lib.common as common

module = '100fm'

def GetCategories(iconimage):
	categories = [
		{'name': 'ערוצים פופולרים', 'cat': 'popular'},
		{'name': 'ערוצים דיגיטלים', 'cat': 'digital'},
		{'name': 'ערוצי תוכן', 'cat': 'content'}
	]
	for category in categories:
		name = common.GetLabelColor(category['name'], keyColor="prColor", bold=True)
		common.addDir(name, category['cat'], 1, iconimage, infos={"Title": name}, module=module)

def GetPlaylists(cat):
	userAgent = common.GetUserAgent()
	playlist = common.OpenURL('http://digital.100fm.co.il/app/', headers={"User-Agent": userAgent}, responseMethod='json')
	for item in playlist['stations']:
		if cat != 'content':
			if item.get('tag', '') == 'content':
				continue
			if cat == 'popular':
				if item.get('popular', '') != 'true':
					continue
			else:
				if item.get('popular', '') == 'true':
					continue
		else:
			if item.get('tag', '') != 'content':
				continue
		name = common.GetLabelColor(item['name'], keyColor="chColor") 
		common.addDir(name, item['audio'], 2, item['cover'], infos={"Title": name, "Plot": item['description']}, module=module, isFolder=False, isPlayable=True)

def Play(name, url, iconimage, quality='best'):
	final = '{0}|User-Agent={1}'.format(url, common.GetUserAgent())
	common.PlayStream(final, quality, name, iconimage)

def WatchLive(url, name='', iconimage='', quality='best'):
	userAgent = common.GetUserAgent()
	headers = {"User-Agent": userAgent}
	channels = common.GetChannelsLinks("radio", module)
	link = channels['link']
	try:
		playlist = common.OpenURL(channels['ch'], headers={"User-Agent": userAgent}, responseMethod='json')
		link = playlist['stations'][0]['audio']
	except Exception as ex:
		xbmc.log(str(ex), 3)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 0:		#------------- Series: ---------------
		GetCategories(iconimage)
	elif mode == 1:		#------------- Episodes: -----------------
		GetPlaylists(url)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
	elif mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')