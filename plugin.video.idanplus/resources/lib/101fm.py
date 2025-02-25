# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = '101fm'

def WatchLive(url, name='', iconimage='', quality='best'):
	userAgent = common.GetUserAgent()
	headers = {"User-Agent": userAgent}
	channels = common.GetChannelsLinks("radio", module)
	link = channels['link']
	try:
		text = common.OpenURL(channels['ch'], headers=headers)
		match = re.compile('<iframe.*?player/(.*?)/').findall(text)
		url = channels['tunein'].format(match[0])
		data = common.OpenURL(url, headers=headers, responseMethod='json')
		link = data['body']['url']
	except Exception as ex:
		xbmc.log(str(ex), 3)
		
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')