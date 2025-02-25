# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = '1064fm'
baseUrl = 'https://radio1064.co.il'
userAgent = common.GetUserAgent()
headers = {"User-Agent": userAgent}

def GetPodcatsList(iconimage, page='1'):
	page = int(page)
	url = '{0}/podcasts?category=&person=&show=&order=updated--dn&page={{0}}'.format(baseUrl)
	xbmc.log(url.format(page), 5)
	text = common.OpenURL(url.format(page), headers=headers)
	podcasts, pagination = re.compile('container container--big(.*?)class="pagination">(.*?)</section>', re.S).findall(text)[0]
	podcasts = re.compile('<a href="(.*?)".*?data-src="(.*?)".*?podcastCard__title">(.*?)</div>.*?podcastCard__description">(.*?)</div>', re.S).findall(podcasts)
	for link, icon, name, desc in podcasts:
		name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="prColor", bold=True)
		desc = common.GetLabelColor(desc, keyColor="chColor")
		common.addDir(name, '{0}{1}'.format(baseUrl, link), 2, icon, infos={"Plot": desc, "Title": name}, module=module, isFolder=False, isPlayable=True)
	pagination = re.compile('href=.*?page=(.*?)"', re.S).findall(pagination)
	pages = page
	for p in pagination:
		if int(p) > pages:
			pages = int(p)
	if page > 1:
		name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
		common.addDir(name, str(page-1), 0, iconimage, infos={"Title": name, "Plot": name}, module=module)
	if pages > page:
		name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
		common.addDir(name, str(page+1), 0, iconimage, infos={"Title": name, "Plot": name}, module=module)
	if pages > 1:
		name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
		common.addDir(name, 'p={0}&pages={1}'.format(page, pages), 1, iconimage, infos={"Title": name, "Plot": name}, module=module)

def Play(name, url, iconimage, quality='best'):
	text = common.OpenURL(url, headers=headers)
	link = re.compile('<audio controls="controls" src="(.*?)"').findall(text)[0]
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = common.GetChannelsLinks("radio", module)
	link = channels['link']
	try:
		text = common.OpenURL(channels['ch'], headers=headers)
		link = re.compile('"webapp\.broadcast_link":"(.*?)"').findall(text)[0]
		link = link.replace('\\u002F', '/')
	except Exception as ex:
		xbmc.log(str(ex), 3)

	link = common.GetStreams(link, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)
	
def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 0:		#------------- Podcats: ---------------
		if url is None or url == '':
			url = '1'
		GetPodcatsList(iconimage, url)
	elif mode == 1:		#--- Move to a specific episodes' page  --
		prms = common.parse_qs(url)
		page = common.GetIndexFromUser(name, int(prms['pages'][0]))
		if page == 0:
			page = int(prms['p'][0])
		GetPodcatsList(iconimage, page)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
	elif mode == 11:
		WatchLive(url, name, iconimage, moreData)		# Playing Live
		
	common.SetViewMode('episodes')
