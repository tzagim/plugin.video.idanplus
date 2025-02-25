# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = '99fm'

def GetCategories():
	text = common.OpenURL('http://eco99fm.maariv.co.il/RSS_MusicChannels_Index/')
	rss = common.XmlToDict(text)
	for item in rss['rss']['channel']['item']:
		name = common.GetLabelColor(item['title'], keyColor="prColor", bold=True)
		image = GetImage(re.compile("src='(.+?)'").findall(item['description'])[0])
		common.addDir(name, item['link'], 1, image, infos={"Title": name, "Plot": item['itunes:summary']}, module=module)

def GetPlaylists(url):
	text = common.OpenURL(url)
	rss = common.XmlToDict(text)
	for item in rss['rss']['channel']['item']:
		name = common.GetLabelColor(item['title'], keyColor="chColor") 
		image = GetImage(re.compile("src='(.+?)'").findall(item['description'])[0])
		common.addDir(name, item['link'], 2, image, infos={"Title": name, "Plot": item['itunes:summary']}, module=module, isFolder=False, isPlayable=True)

def GetImage(image):
	image = image.replace(u'\u200F', '')
	return image[image.rfind('http'):]

def Play(name, url, iconimage, quality='best'):
	userAgent = common.GetUserAgent()
	playlist = common.OpenURL(url.replace('playlist', 'api/v1/public/playlist'), headers={"User-Agent": userAgent}, responseMethod='json')
	final = '{0}|User-Agent={1}'.format(playlist['item']['url'], userAgent)
	common.PlayStream(final, quality, name, iconimage)

def WatchLive(name='', iconimage='', quality='best'):
	link = common.GetChannelsLinks("radio", module)
	final = '{0}|User-Agent={1}'.format(link, common.GetUserAgent())
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 0:		#------------- Series: ---------------
		GetCategories()
	elif mode == 1:		#------------- Episodes: -----------------
		GetPlaylists(url)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
	if mode == 11:
		WatchLive(name, iconimage, moreData)
		
	common.SetViewMode('episodes')