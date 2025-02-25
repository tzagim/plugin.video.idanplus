# -*- coding: utf-8 -*-
import xbmc
import re 
import resources.lib.common as common

module = 'hidabroot'

def WatchLive(name='', iconimage='', quality='best'):
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	url = common.GetChannelsLinks("tv", module)
	text = common.OpenURL(url, headers=headers)
	match = re.compile('<source\s*?src="(.*?)"', re.S).findall(text)
	#text = common.OpenURL('https://go.shidur.net/player/testlive.php', headers=headers)
	#match = re.compile('hls\.loadSource\(["\'](.*?)["\']\)').findall(text)
	link = common.GetStreams(match[0], headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(name, iconimage, moreData)
		
	common.SetViewMode('episodes')