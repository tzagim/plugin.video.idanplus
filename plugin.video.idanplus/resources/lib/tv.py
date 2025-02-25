# -*- coding: utf-8 -*-
import re
import resources.lib.common as common

module = 'tv'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("tv", module)
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	regex = channels[url].get('regex')
	if regex:
		text = common.OpenURL(channels[url]['link'], headers=headers)
		link = re.compile(regex, channels[url].get('flags', 0)).findall(text)
		if len(link) > 0:
			link = link[0]
		else:
			link = channels[url]['direct']
	else:
		link = channels[url]['link']
	if link.startswith('//'):
		link = 'http:{0}'.format(link)
	referer = channels[url].get('referer')
	if referer:
		headers['referer'] = referer
	if not channels[url].get('final') == True:
		link = common.GetStreams(link, headers=headers, quality=quality)
	if referer:
		common.PlayStream('{0}|User-Agent={1}&Referer={2}'.format(link, userAgent, referer), quality, name, iconimage)
	else:
		common.PlayStream('{0}|User-Agent={1}'.format(link, userAgent), quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')