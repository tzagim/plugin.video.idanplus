# -*- coding: utf-8 -*-
import re
import resources.lib.common as common

module = 'radio'

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
		link = re.compile(regex, linkDetails.get('flags', 0)).findall(text)[0]

	if link.find('://') < 0:
		link = 'http://' + link
	
	final = '{0}|User-Agent={1}&verifypeer=false'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')