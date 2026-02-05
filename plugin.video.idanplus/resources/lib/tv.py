# -*- coding: utf-8 -*-
import re
import resources.lib.common as common

module = 'tv'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("tv", module)
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	channel = channels[url]
	regex = channel.get('regex')
	link = channel['link']
	if regex:
		text = common.OpenURL(link, headers=headers)
		link = re.compile(regex, channel.get('flags', 0)).findall(text)
		if len(link) > 0:
			link = link[0]
		else:
			link = channel['direct']

	if link.startswith('//'):
		link = 'http:{0}'.format(link)
	referer = channel.get('referer')
	if referer:
		headers['referer'] = referer
	if not channel.get('final') == True:
		link = common.GetStreams(link, headers=headers, quality=quality)
	
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	if referer:
		final = '{0}&Referer={1}'.format(final, referer)

	manifest_type = channel.get('manifest_type')
	if manifest_type is None:
		common.PlayStream(final, quality, name, iconimage)
	else:
		common.PlayStream(final, quality, name, iconimage, adaptive=True, manifest_type=manifest_type)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')