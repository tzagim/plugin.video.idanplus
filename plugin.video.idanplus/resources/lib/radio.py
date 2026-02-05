# -*- coding: utf-8 -*-
import re
import resources.lib.common as common

module = 'radio'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("radio", module)
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	channel = channels[url]
	regex = channel.get('regex')
	link = channel['link']
	if regex:
		text = common.OpenURL(link, headers=headers)
		link = re.compile(regex, channel.get('flags', 0)).findall(text)[0]

	if link.find('://') < 0:
		link = 'http://' + link
	
	final = '{0}|User-Agent={1}&verifypeer=false'.format(link, userAgent)
	manifest_type = channel.get('manifest_type')
	if manifest_type is None:
		common.PlayStream(final, quality, name, iconimage)
	else:
		common.PlayStream(final, quality, name, iconimage, adaptive=True, manifest_type=manifest_type)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')