# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import re, json
import resources.lib.common as common

module = '891fm'

def GetSeriesList(iconimage):
	text = common.OpenURL('https://www.oles.tv/891fm/shows/')
	series = re.compile('class="media-left"><a href="(.*?)" class="pic link"><img class="media-object" src="(.*?)" alt="Programme: (.*?)"(.*?)<div class="tools">').findall(text)
	for link, iconimage, name, desc in series:
		name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="prColor", bold=True)
		match = re.compile('p class="text">(.*?)<a').findall(desc)
		desc = common.GetLabelColor(match[0], keyColor="chColor") if len(match) > 0 else ''
		common.addDir(name, link, 1, iconimage, infos={"Plot": desc, "Title": name}, module=module)

def GetEpisodesList(url, programName, image):
	programName = common.GetLabelColor(programName, keyColor="prColor")
	text = common.OpenURL(url)
	match = re.compile('class="day">(.*?)class="tools"').findall(text)
	episodes = re.compile('<a href="(.*?)".*?</i>\s*(.*?)</a>').findall(match[0])
	name = common.GetLabelColor(programName, keyColor="prColor") 
	common.addDir(name, '', 99, image, infos={"Title": name, "Plot": name}, module=module, isFolder=False)
	grids_arr = []
	for link, name in episodes:
		grids_arr.append((name, link))
	grids_sorted = sorted(grids_arr,key=lambda grids_arr: grids_arr[0], reverse=True)
	for name, link in grids_sorted:
		name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="chColor")
		common.addDir(name, link, 2, image, infos={"Title": name, "Plot": programName}, module=module, isFolder=False, isPlayable=True)

def Play(name, url, iconimage, quality='best'):
	userAgent = common.GetUserAgent()
	headers = {"User-Agent": userAgent}
	text = common.OpenURL(url, headers=headers)
	match = re.compile('DATA\s*=\s*{(.*?)};').findall(text)
	result = json.loads('{' + match[0] + '}')
	hour = url[url.find('?play=')+6:]
	link = result[hour]['stream']
	#link = common.GetStreams(match[0], headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 0:		#------------- Series: ---------------
		GetSeriesList(iconimage)
	elif mode == 1:		#------------- Episodes: -----------------
		GetEpisodesList(url, name, iconimage)
	elif mode == 2:		#------------- Playing episode  ----------
		Play(name, url, iconimage, moreData)
		
	common.SetViewMode('episodes')
