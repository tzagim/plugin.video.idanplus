# -*- coding: utf-8 -*-
import xbmc
import resources.lib.common as common

module = 'glz'
apiUrl = 'https://glz.co.il/umbraco/api/'
userAgent = common.GetUserAgent()
headers = {"User-Agent": userAgent}
channels = common.GetChannelsLinks("radio", module)

def GetPlaylists(url):
	url = '{0}player/getplayerdata?rootId={1}'.format(apiUrl, channels[url]['rootId'])
	playlist = common.OpenURL(url, headers=headers, responseMethod='json')
	for item in playlist['musicChannels']:
		name = common.GetLabelColor(item['name'], keyColor="chColor") 
		common.addDir(name, item['fileUrl'], 2, 'https://glz.co.il{0}'.format(item['playerImage']), infos={"Title": name}, module=module, isFolder=False, isPlayable=True)

def Play(name, url, iconimage, quality='best'):
	link = common.GetRedirect(url, headers=headers)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def WatchLive(url, name='', iconimage='', quality='best'):
	link = channels[url]['live']
	try:
		url = '{0}player/getplayerdata?rootId={1}'.format(apiUrl, channels[url]['rootId'])
		data = common.OpenURL(url, headers=headers, responseMethod='json')
		liveBroadcast = data['liveBroadcast']['fileUrl']
		if liveBroadcast is not None:
			liveBroadcast = common.GetRedirect(data['liveBroadcast']['fileUrl'], headers=headers)
			if liveBroadcast is not None:
				link = liveBroadcast
	except Exception as ex:
		xbmc.log(str(ex), 3)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 1:		#------------- Episodes: -----------------
		GetPlaylists(url)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
	elif mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')