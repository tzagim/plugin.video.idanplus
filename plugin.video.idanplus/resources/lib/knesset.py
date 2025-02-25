# -*- coding: utf-8 -*-
import resources.lib.common as common

module = 'knesset'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("tv", module)
	url = channels[url]
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	link = common.GetStreams(url, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')
