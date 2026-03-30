# -*- coding: utf-8 -*-
import re
import resources.lib.common as common

module = 'tv'

def WatchLive(channelID, name='', iconimage='', quality='best'):
	channel = common.GetChannel(channelID)
	isAdaptive = common.GetChannelAdaptive(channel)
	linkDetails = channel.get('linkDetails')
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	regex = linkDetails.get('regex')
	link = linkDetails['link']
	if regex:
		text = common.OpenURL(link, headers=headers)
		link = re.compile(regex, linkDetails.get('flags', 0)).findall(text)
		if len(link) > 0:
			link = link[0]
		else:
			link = linkDetails['direct']
	if link.startswith('//'):
		link = 'http:{0}'.format(link)
	referer = linkDetails.get('referer')
	if referer:
		headers['referer'] = referer
	if not linkDetails.get('final') == True:
		link = common.GetStreams(link, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	if referer:
		final = '{0}&Referer={1}'.format(final, referer)
	common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')