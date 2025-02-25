# -*- coding: utf-8 -*-
import re, json
import resources.lib.common as common

module = 'walla'
baseUrl = 'https://www.walla.co.il'

def WatchLive(name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("tv", module)
	link = channels['link']
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	text = common.OpenURL(baseUrl, headers=headers)
	match = re.compile('<video.*?src="(.*?)"').findall(text)
	if len(match) > 0:
		link = common.GetRedirect(match[0], headers=headers)
	link = common.GetStreams(link, headers=headers, quality=quality)
	common.PlayStream('{0}|User-Agent={1}'.format(link, userAgent), quality, name, iconimage)
	
def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(name, iconimage, moreData)
		
	common.SetViewMode('episodes')