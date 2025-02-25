# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = 'radio'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("radio", module)
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	regex = channels[url].get('regex')
	if regex:
		text = common.OpenURL(channels[url]['link'], headers=headers)
		link = re.compile(channels[url]['regex'], channels[url].get('flags', 0)).findall(text)[0]
	else:
		link = channels[url]['link']
	if link.find('://') < 0:
		link = 'http://' + link

	final = '{0}|User-Agent={1}&verifypeer=false'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')