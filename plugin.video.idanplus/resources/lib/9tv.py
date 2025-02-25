# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = '9tv'
moduleIcon = common.GetIconFullPath("9tv.png")
baseUrl = 'http://www.9tv.co.il'

def GetSeriesList(iconimage):
	text = common.OpenURL('{0}/allprograms'.format(baseUrl))
	series = re.compile('<li class=".*?programs">(.*?)</li>', re.S).findall(text)
	for serie in series:
		matches = re.compile('href="(.*?)".*?"background\-image: url\((.*?)\)".*?title="(.*?)".*?"program_tv_title">(.*?)</.*?<div>(.*?)</', re.S).findall(serie)
		for link, image, actor, name, description in matches:
			name = common.GetLabelColor(name, keyColor="prColor", bold=True)
			common.addDir(name, '{0}{1}'.format(baseUrl, link), 1, '{0}{1}'.format(baseUrl, image), infos={"Title": name, "Plot": description}, module=module)

def GetEpisodesList(url, progName=''):
	text = common.OpenURL(url)
	
	pagination = re.compile('pagination\(\d*?, (\d*?)\);', re.S).findall(text)
	pages = 1 if len(pagination) < 1 else int(pagination[0])
	
	i = url.find('program/')
	if i < 1:
		i = url.find('programs/')
		j = url.find('/', i+9)
	else:
		j = url.find('/', i+8)
	if j > 0:
		page = int(url[j+1:])
		_url = url[:j+1]
	else:
		page = 1
		_url = '{0}/'.format(url)

	firstepisode = re.compile('poster: \'(.*?)\',.*?<div>(.*?)</div>.*?<div class="share_group".*?href="(.*?)"', re.S).findall(text)
	for image, name, link in firstepisode:
		name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="chColor")
		common.addDir(name, 'http://{0}'.format(link), 2, '{0}{1}'.format(baseUrl, image), infos={"Title": name, "Plot": progName}, module=module, isFolder=False, isPlayable=True)
	
	episodes = re.compile('<li class=".*?program">(.*?)</li>', re.S).findall(text)
	for episode in episodes:
		matches = re.compile('href="(.*?)".*?src="(.*?)".*?program_item_date">(.*?)</', re.S).findall(episode)
		for link, image, name in matches:
			name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="chColor")
			common.addDir(name, '{0}{1}'.format(baseUrl, link), 2, '{0}{1}'.format(baseUrl, image), infos={"Title": name, "Plot": progName}, module=module, isFolder=False, isPlayable=True)
	
	if page > 1:
		name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
		common.addDir(name, '{0}{1}'.format(_url, page-1), 1, image, infos={"Title": name, "Plot": name}, module=module)
	if pages > page:
		name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
		common.addDir(name, '{0}{1}'.format(_url, page+1), 1, image, infos={"Title": name, "Plot": name}, module=module)
	if pages > 1:
		name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
		common.addDir(name, '{0}?p={1}&pages={2}'.format(_url, page, pages), 3, image, infos={"Title": name, "Plot": name}, module=module)
	
def Play(name, url, iconimage, quality='best'):
	userAgent = common.GetUserAgent()
	headers = {"User-Agent": userAgent}
	text = common.OpenURL(url, headers=headers)
	match = re.compile('program_main_item.*?src="(.*?)"', re.S).findall(text)
	if match == []:
		match = re.compile('<source src="(.*?)"').findall(text)
	if match == []:
		return
	if 'youtube' in match[0] or 'youtu.be' in match[0]:
		final = common.GetYouTube(match[0])
	else:
		final = '{0}|User-Agent={1}'.format(match[0].replace(' ', '%20'), userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == -1:
		GetSeriesList(moduleIcon)
	elif mode == 0:		#------------- Series: ---------------
		GetSeriesList(moduleIcon)
	elif mode == 1:		#------------- Episodes: -----------------
		GetEpisodesList(url, name)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
	elif mode == 3:		#--- Move to a specific episodes' page  --
		urlp = common.url_parse(url)
		prms = common.parse_qs(urlp.query)
		page = common.GetIndexFromUser(name, int(prms['pages'][0]))
		if page == 0:
			page = int(prms['p'][0])
		url = '{0}{1}{2}'.format(baseUrl, urlp.path, page)
		GetEpisodesList(url)
		
	common.SetViewMode('episodes')
