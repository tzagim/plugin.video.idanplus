# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, os, io, random, re, json, urllib

try:
	# For Python 3.0 and later
	import urllib.parse as urlparse
	py2 = False
except ImportError:
	# Fall back to Python 2
	py2 = True
	import urlparse

AddonID = 'plugin.video.idanplus'
Addon = xbmcaddon.Addon(AddonID)
icon = Addon.getAddonInfo('icon')
AddonVer = Addon.getAddonInfo('version')
AddonName = "Idan Plus"

def decode(text, dec, force=False):
	if py2:
		text = text.decode(dec)
	elif force:
		text= bytearray(text, 'utf-8').decode(dec)
	return text

def encode(text, dec):
	if py2:
		text = text.encode(dec)
	return text

def translatePath(path):
	if py2:
		text = xbmc.translatePath(path)
	else:
		import xbmcvfs
		text = xbmcvfs.translatePath(path)
	return text

profileDir = decode(translatePath(Addon.getAddonInfo("profile")), "utf-8")
if not os.path.exists(profileDir):
	os.makedirs(profileDir)

imagesDir = decode(translatePath(os.path.join(Addon.getAddonInfo('path'), 'resources', 'images')), "utf-8")
epgFile = os.path.join(profileDir, 'epg.json')
seriesFile = os.path.join(profileDir, 'series.json')
seriesUrl = 'https://raw.githubusercontent.com/Fishenzon/repo/master/zips/plugin.video.idanplus/series.json.zip'
youtubePlugin = 'plugin://plugin.video.youtube'

userAgents = [
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.1',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.',
	'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.6',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.2',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.4',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.',
	'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 10; MAR-LX1A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 15_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 16_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.66 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/300.0.598994205 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 10; YAL-L21; HMSCore 6.13.0.302; GMSCore 24.02.13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 HuaweiBrowser/14.0.2.311 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 11; moto e20 Build/RONS31.267-94-14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G990B2) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-A528B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.3',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/120.0.2210.144',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox One) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edge/44.18363.8131',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0',
	'Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/120.0.2210.144',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:115.0) Gecko/20100101 Firefox/115.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
	'Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/122.0',
	'Mozilla/5.0 (X11; Linux i686; rv:115.0) Gecko/20100101 Firefox/115.0',
	'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:115.0) Gecko/20100101 Firefox/115.0',
	'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
	'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.66 Mobile/15E148 Safari/604.1',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 EdgiOS/120.2210.150 Mobile/15E148 Safari/605.1.15',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/15E148 Safari/605.1.15',
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
	'Mozilla/5.0 (iPod; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.66 Mobile/15E148 Safari/604.1',
	'Mozilla/5.0 (iPod touch; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) FxiOS/122.0 Mobile/15E148 Safari/605.1.15',
	'Mozilla/5.0 (iPod touch; CPU iPhone 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
	'Mozilla/5.0 (iPad; CPU OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/122.0 Mobile/15E148 Safari/605.1.15',
	'Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
	'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 EdgA/120.0.2210.141',
	'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 EdgA/120.0.2210.141',
	'Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 EdgA/120.0.2210.141',
	'Mozilla/5.0 (Linux; Android 10; ONEPLUS A6003) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 EdgA/120.0.2210.141',
	'Mozilla/5.0 (Windows Mobile 10; Android 10.0; Microsoft; Lumia 950XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 Edge/40.15254.603',
	'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/122.0 Firefox/122.0',
	'Mozilla/5.0 (Android 14; Mobile; LG-M255; rv:122.0) Gecko/122.0 Firefox/122.0',
	'Mozilla/5.0 (Linux; Android 10; VOG-L29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 OPR/76.2.4027.73374',
	'Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 OPR/76.2.4027.73374',
	'Mozilla/5.0 (Linux; Android 10; SM-N975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36 OPR/76.2.4027.73374',
	'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-S908U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-A536U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 13; SM-A515U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 12; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
	'Mozilla/5.0 (Linux; Android 12; SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
]
userAgent = random.choice(userAgents)


def GetAddon():
	Addon = xbmcaddon.Addon(AddonID)
	return Addon

def GetAddonSetting(key):
	Addon = xbmcaddon.Addon(AddonID)
	value = Addon.getSetting(key)
	if '_res' in key:
		if value == '':
			value = 'best'
	return value

def SetAddonSetting(key, value):
	Addon.setSetting(key, value)

def GetHandle():
	try:
		handle = int(sys.argv[1])
	except:
		handle = -1
	return handle

def GetIconFullPath(icon):
	return os.path.join(imagesDir, icon)

def GetKodiVer():
	return float(re.split(' |\-',xbmc.getInfoLabel('System.BuildVersion'))[0])

def NewerThanPyVer(ver):
	runnigVer = ver.split('.')
	for i in range(len(runnigVer)):
		if sys.version_info[i] > int(runnigVer[i]):
			return True
	return False

def IsAddonInstalled(addonid):
	return xbmc.getCondVisibility('System.HasAddon({0})'.format(addonid)) == 1

def InstallAddon(addonid):
	xbmc.executebuiltin('InstallAddon({0})'.format(addonid))

def IsAddonEnabled(addonid):
	return json.loads(xbmc.executeJSONRPC('{{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","params":{{"addonid":"{0}", "properties": ["enabled"]}},"id":1}}'.format(addonid)))['result']['addon']['enabled']

def EnableAddon(addonid):
	if GetKodiVer() >= 19:
		xbmc.executebuiltin('EnableAddon({0})'.format(addonid))
	else:
		xbmc.executeJSONRPC('{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{{"addonid":"{0}","enabled":true}},"id":1}}'.format(addonid))

def DisableAddon(addonid):
	xbmc.executeJSONRPC('{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{{"addonid":"{0}","enabled":false}},"id":1}}'.format(addonid))

def GetTextFile(filename):
	content = ''
	if os.path.isfile(filename):
		with io.open(filename, 'r', encoding="utf-8") as f:
			content = f.read()
	return content

def ReadList(fileName):
	import collections
	try:
		with io.open(fileName, 'r', encoding='utf-8') as f:
			content = json.load(f, object_pairs_hook=collections.OrderedDict) if NewerThanPyVer('2.6.99') else json.load(f)
	except Exception as ex:
		xbmc.log(str(ex), 3)
		content=[]
	return content

def WriteList(filename, list):
	try:
		with io.open(filename, 'w', encoding='utf-8') as f:
			f.write(uni_code(json.dumps(list, indent=2, ensure_ascii=False)))
		success = True
	except Exception as ex:
		xbmc.log(str(ex), 3)
		success = False
	return success

def isFileOld(filename, deltaInSec=86400):
	import time
	lastUpdate = 0 if not os.path.isfile(filename) else int(os.path.getmtime(filename))
	return (time.time() - lastUpdate) > deltaInSec

def GetUserAgent():
	return userAgent

def GetSession():
	import requests
	return requests.session()

def OpenURL(url, headers={}, user_data=None, session=None, cookies=None, retries=1, responseMethod='text', verify=True):
	link = ""
	import requests
	if headers.get('Accept-encoding', '') == '':
		headers['Accept-encoding'] = 'gzip'
	if headers.get('User-agent', '') == '':
		headers['User-agent'] = userAgent
	if headers.get('User-Agent', '') == '':
		headers['User-Agent'] = userAgent
	for i in range(retries):
		try:
			if session is None:
				if user_data is None:
					response = requests.get(url, headers=headers, cookies=cookies, verify=verify)
				else:
					response = requests.post(url, headers=headers, cookies=cookies, data=user_data, verify=verify)
			else:
				if user_data is None:
					response = session.get(url, headers=headers, cookies=cookies, verify=verify)
				else:
					response = session.post(url, data=user_data, headers=headers, cookies=cookies, verify=verify)
			if responseMethod == 'text':
				if int(response.status_code) > 400:
					xbmc.log('{0}  -  response {1}.'.format(url, response.status_code), 3)
					xbmc.log(response.text, 3)
					continue
				link = response.text
			elif responseMethod == 'content':
				link = response.content
			elif responseMethod == 'json':
				link = response.json()
			break
		except Exception as ex:
			xbmc.log(str(ex), 3)
			return None
	return link

def GetRedirect(url, headers={}):
	try:
		import requests
		response = requests.head(url, headers=headers, allow_redirects=False)
		if response.status_code in set([301, 302, 303, 307]) and 'location' in response.headers:
			url = response.headers['location']
		if response.status_code >= 400 and response.status_code < 500:
			url = None
	except Exception as ex:
		xbmc.log(str(ex), 3)
	return url

def addDir(name, url, mode, iconimage='DefaultFolder.png', infos=None, contextMenu=None, module='', moreData='', totalItems=None, isFolder=True, isPlayable=False, addFav=True, urlParamsData={}):
	urlParams = {'name': name.replace('?', '|||'), 'url': quote_plus(url), 'mode': mode, 'iconimage': quote_plus(iconimage), 'module': module, 'moredata': quote_plus(moreData)}
	u = '{0}?{1}'.format(sys.argv[0], urlencode(urlParams))
	try:
		listitem = xbmcgui.ListItem(name)
		listitem.setArt({'thumb' : iconimage, 'fanart': iconimage, 'icon': iconimage})
	except:
		listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
	if infos is not None:
		listitem.setInfo(type="Video", infoLabels=infos)
	if isPlayable:
		listitem.setProperty("IsPlayable", "true")
	for param in list(urlParamsData.keys()):
		urlParams[param] = urlParamsData[param].replace('?', '|||')
	if addFav:
		urlParams['isFolder'] = isFolder
		urlParams['isPlayable'] = isPlayable
		item = (GetLocaleString(30026), 'RunPlugin({0}?url={1}&mode=8)'.format(sys.argv[0], quote_plus(urlencode(urlParams))))
		if contextMenu is None:
			contextMenu = [item]
		else:
			contextMenu.append(item)
	item2 = (GetLocaleString(32004), 'RunPlugin({0}?mode=16)'.format(sys.argv[0]))

	if contextMenu is None:
		contextMenu = [item2]
	else:
		contextMenu.append(item2)
	if contextMenu is not None:
		listitem.addContextMenuItems(items=contextMenu)
	handle = GetHandle()
	if totalItems is None:
		xbmcplugin.addDirectoryItem(handle=handle, url=u, listitem=listitem, isFolder=isFolder)
	else:
		xbmcplugin.addDirectoryItem(handle=handle, url=u, listitem=listitem, isFolder=isFolder, totalItems=totalItems)

def DelFile(aFile):
	try:
		if os.path.isfile(aFile):
			os.unlink(aFile)
	except Exception as ex:
		xbmc.log(str(ex), 3)

def DelCookies():
	tempDir = decode(translatePath('special://temp/'), "utf-8")
	for the_file in os.listdir(tempDir):
		if not '.fi' in the_file and the_file != 'cookies.dat':
			continue
		DelFile(os.path.join(tempDir, the_file))

def GetStreams(url, headers={}, user_data=None, session=None, retries=1, quality='best'):
	if quality.startswith('set'):
		addonKey = quality[4:]
		quality = 'set'
	base = urlparse.urlparse(url)
	baseUrl = '{0}://{1}{2}'.format(base.scheme, base.netloc, base.path)
	text = OpenURL(url, headers=headers, user_data=user_data, session=session, retries=retries)
	if text is None:
		return url
	resolutions = [x for x in re.compile('^#EXT-X-STREAM-INF:.*?BANDWIDTH=(\d+)(.*?)\n(.*?)$', re.M).findall(text)]
	resolutions = sorted(resolutions,key=lambda resolutions: int(resolutions[0]), reverse=True)
	link = url
	if quality == 'best':
		for resolution in resolutions:
			link = resolution[2].strip()
			if not link.startswith('http'): 
				link = urlparse.urljoin(baseUrl, link)
				if base.query != '':
					link = '{0}?{1}'.format(link, base.query)
			check = OpenURL(link, headers=headers, user_data=user_data, session=session, retries=retries)
			if check is not None:
				break
	elif quality == 'choose' or quality == 'set':
		if quality == 'set':
			resolutions.insert(0, (GetLocaleString(30024), '', ''))
		resNames = []
		for item in resolutions:
			resNames.append(item[0]) 
			if 'RESOLUTION' in item[1]:
				resNames[-1] += '  [{0}]'.format(re.compile('RESOLUTION=(\d+)x(\d+)').findall(item[1])[0][1])
			elif 'NAME' in item[1]:
				resNames[-1] += '  [{0}]'.format(re.compile('NAME="(.*?)"').findall(item[1])[0])
		qualityInd = xbmcgui.Dialog().select(GetLocaleString(30005), resNames)
		if qualityInd > -1:
			if quality == 'set':
				Addon.setSetting(addonKey, '' if qualityInd == 0 else resolutions[qualityInd][0])
			link = resolutions[qualityInd][2]
	else:
		quality = int(quality)
		res = 0
		for resolution in resolutions:
			_res = int(resolution[0])
			if _res >=  res and _res <=  quality:
				res = _res
				link = resolution[2]
	if not link.startswith('http'): 
		link = urlparse.urljoin(baseUrl, link)
	if base.query != '' and base.query not in link:
		link = '{0}?{1}'.format(link, base.query)
	return link

def PlayStream(url, quality='best', name='', iconimage=''):
	plot = xbmc.getInfoLabel("ListItem.Plot")
	year = xbmc.getInfoLabel("ListItem.Year")
	infos = {"title": name, "plot": plot, "year": year,u'mpaa':'heb'}
	if 'dailymotion' in url:
		url = GetDailymotion(url)
	try:
		listitem = xbmcgui.ListItem(name, path=url)
		listitem.setArt({'thumb' : iconimage, 'fanart': iconimage, 'icon': iconimage})
	except:
		listitem = xbmcgui.ListItem(name, path=url, iconImage=iconimage, thumbnailImage=iconimage)
	listitem.setInfo(type="Video", infoLabels=infos)
	if (quality == 'choose' or quality.startswith('set')) and '.m3u8' in url:
		xbmc.Player().play(url, listitem)
	else:
		xbmcplugin.setResolvedUrl(handle=GetHandle(), succeeded=True, listitem=listitem)

def GetLocaleString(id):
	return encode(Addon.getLocalizedString(id), 'utf-8')

def EscapeXML(text):
	return text.replace('&', '&amp;').replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

def UnEscapeXML(st):
	import xml.parsers.expat as expat
	st = st.replace("&hellip;", "").replace("&nbsp;", " ")
	want_unicode = False
	if py2 and isinstance(st, unicode):
		st = encode(st, "utf-8")
		want_unicode = True
	# the rest of this assumes that `st` is UTF-8
	list = []
	# create and initialize a parser object
	p = expat.ParserCreate("utf-8")
	p.buffer_text = True
	if py2:
		p.returns_unicode = want_unicode
	p.CharacterDataHandler = list.append
	# parse the data wrapped in a dummy element
	# (needed so the "document" is well-formed)
	p.Parse("<e>", 0)
	p.Parse(st, 0)
	p.Parse("</e>", 1)
	# join the extracted strings and return
	es = ""
	if want_unicode:
		es = u""
	return es.join(list)

def XmlToDict(text):
	import xmltodict
	return xmltodict.parse(text)

def GetLabelColor(text, keyColor=None, bold=False, color=None):
	if not color:
		color = Addon.getSetting(keyColor)
	if bold and Addon.getSetting("boldLables") == "true":
		text = '[B]{0}[/B]'.format(text)
	return text if color == 'none' else '[COLOR {0}]{1}[/COLOR]'.format(color, text)

def getDisplayName(title, subtitle, programNameFormat, bold=False):
	if programNameFormat == 0:
		displayName = ' {0} - {1} '.format(GetLabelColor(title, keyColor="prColor", bold=bold) , GetLabelColor(subtitle, keyColor="chColor"))
	elif programNameFormat == 1:
		displayName = ' {0} - {1} '.format(GetLabelColor(subtitle, keyColor="chColor") , GetLabelColor(title, keyColor="prColor", bold=bold))
	return displayName

def GetUnColor(text):
	regex = re.compile("(\[/?(?:COLOR|B).*?\])", re.IGNORECASE)
	return regex.sub('', text).strip()

def GetImageUrl(iconimage):
	if iconimage is not None:
		i = iconimage.find('://')
		iconimage = iconimage[:i+3] + quote(encode(iconimage[i+3:], "utf-8"))
	return iconimage

def SetViewMode(content):
	xbmcplugin.setContent(GetHandle(), content)
	viewMode = Addon.getSetting("viewModeEpisodes").strip()
	if viewMode != 'Auto' and viewMode != '':
		xbmc.executebuiltin("Container.SetViewMode({0})".format(viewMode))

def ToggleSortMethod(id, sortBy):
	if sortBy == 0:
		Addon.setSetting(id, "1")
	else:
		Addon.setSetting(id, "0")
	xbmc.executebuiltin("Container.Refresh()")

def GetIntSetting(k, v=0):
	if not Addon.getSetting(k).isdigit():
		Addon.setSetting(k, str(v))
	return int(Addon.getSetting(k))

def MoveInList(index, step, listFile):
	theList = ReadList(listFile)
	if index + step >= len(theList) or index + step < 0:
		return
	if step == 0:
		step = GetIndexFromUser(GetLabelColor(GetLocaleString(30034), bold=True, color="none"), len(theList))
		if step != 0:
			step = step - 1 - index
	if step < 0:
		tempList = theList[0:index + step] + [theList[index]] + theList[index + step:index] + theList[index + 1:]
	elif step > 0:
		tempList = theList[0:index] + theList[index +  1:index + 1 + step] + [theList[index]] + theList[index + 1 + step:]
	else:
		return
	WriteList(listFile, tempList)
	xbmc.executebuiltin("Container.Refresh()")

def GetNumFromUser(title, defaultt=''):
	dialog = xbmcgui.Dialog()
	choice = dialog.input(title, defaultt=defaultt, type=xbmcgui.INPUT_NUMERIC)
	return None if choice is None or choice == '' else int(choice)

def GetIndexFromUser(title, listLen):
	location = GetNumFromUser('{0} (1-{1})'.format(title, listLen))
	return 0 if location is None or location > listLen or location <= 0 else location

def GetUpdatedList(listFile, listUrl, headers={}, deltaInSec=86400, isZip=False, sort=False, decode_text=None):
	if isFileOld(listFile, deltaInSec=deltaInSec):
		try:
			if isZip:
				aFile = '{0}.zip'.format(listFile)
				DelFile(aFile)
			else:
				aFile = listFile
			data = OpenURL(listUrl, headers=headers, responseMethod='content')
			with io.open(aFile, 'wb') as f:
				if decode_text is not None:
					data = data.decode(decode_text).encode('utf-8')
				f.write(data)
			if isZip:
				xbmc.executebuiltin("Extract({0}, {1})".format(aFile, profileDir), True)
				DelFile(aFile)
		except Exception as ex:
			xbmc.log("{0}".format(ex), 3)
	items = ReadList(listFile)
	return sorted(items,key=lambda items: items['name']) if sort else items

def GetChannelsLinks(kind, module, downloadOnly=False):
	channelsFile = os.path.join(profileDir, 'channels.json')
	channelsUrl = 'https://raw.githubusercontent.com/Fishenzon/repo/master/zips/plugin.video.idanplus/channels.json.zip'
	deltaInSec = 0 if downloadOnly else Addon.getSettingInt("updateChannelsLinksInterval")*3600
	channels = GetUpdatedList(channelsFile, channelsUrl, deltaInSec=deltaInSec, isZip=True)
	if (downloadOnly):
		return
	if len(channels) == 0:
		resourcesDir = decode(translatePath(os.path.join(Addon.getAddonInfo('path'), 'resources')), "utf-8")
		channels = ReadList(os.path.join(resourcesDir, 'channels.json'))
	return channels.get(kind, {}).get(module, {}) if len(channels) > 0 else {}

def GetKeyboardText(title = '', defaultText = ''):
	keyboard = xbmc.Keyboard(defaultText, title)
	keyboard.doModal()
	return '' if not keyboard.isConfirmed() else keyboard.getText()

def quote(text):
	if py2:
		return urllib.quote(text)
	else:
		return urlparse.quote(text)

def quoteNonASCII(text):
	t = ''
	for i in range(len(text)):
		t += text[i] if ord(text[i]) < 128 else quote(text[i])
	return t

def unquote(text):
	if py2:
		return urllib.unquote(text)
	else:
		return urlparse.unquote(text)

def quote_plus(text):
	if py2:
		return urllib.quote_plus(text)
	else:
		return urlparse.quote_plus(text)

def unquote_plus(text):
	if py2:
		return urllib.unquote_plus(text)
	else:
		return urlparse.unquote_plus(text)

def urlencode(text):
	if py2:
		return urllib.urlencode(text)
	else:
		return urlparse.urlencode(text)

def parse_qs(text):
	return urlparse.parse_qs(text)

def parse_qsl(text):
	return urlparse.parse_qsl(text)

def url_parse(text):
	return urlparse.urlparse(text)

def urlunparse(text):
	return urlparse.urlunparse(text)

def uni_code(text):
	if py2:
		return unicode(text)
	else:
		return str(text)

def items(d):
	if py2:
		return d.iteritems()
	else:
		return d.items()

def isnumeric(text):
	return uni_code(text).isnumeric()

def GetKaltura(entryId, partnerId, baseUrl, userAgent, quality='best'):
	headers = {
		'accept': '*/*',
		'accept-language': 'en',
		'content-type': 'application/json',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'cross-site',
		'referrer': baseUrl,
		'referrerPolicy': 'strict-origin-when-cross-origin',
		'User-Agent': userAgent
	}
	payload = json.dumps({"1":{"service":"session","action":"startWidgetSession","widgetId":"_{0}".format(partnerId)},"2":{"service":"baseEntry","action":"list","ks":"{1:result:ks}","filter":{"redirectFromEntryId":entryId},"responseProfile":{"type":1,"fields":"id,referenceId,name,description,thumbnailUrl,dataUrl,duration,msDuration,flavorParamsIds,mediaType,type,tags,dvrStatus,externalSourceType,status"}},"3":{"service":"baseEntry","action":"getPlaybackContext","entryId":"{2:result:objects:0:id}","ks":"{1:result:ks}","contextDataParams":{"objectType":"KalturaContextDataParams","flavorTags":"all"}},"4":{"service":"metadata_metadata","action":"list","filter":{"objectType":"KalturaMetadataFilter","objectIdEqual":entryId,"metadataObjectTypeEqual":"1"},"ks":"{1:result:ks}"},"apiVersion":"3.3.0","format":1,"ks":"","clientTag":"html5:v0.56.1","partnerId":partnerId})
	link = ''
	try:
		response = OpenURL("https://cdnapisec.kaltura.com/api_v3/service/multirequest", headers=headers, user_data=payload, responseMethod='json')
		#xbmc.log(str(response[2]["sources"]), 5)
		for s in response[2]["sources"]:
			if s["format"] == "applehttp":
				link = s["url"]
				break
		link = GetStreams(link, quality=quality)
	except Exception as ex:
		xbmc.log(str(ex), 3)
	return link

def s(elem):
	if elem[0] == "auto":
		return 1
	else:
		return int(elem[0].split("@")[0])

def GetDailymotion(url):
	vid = re.compile('.*?video/(.*?)[\?|]').findall(url)
	if len(vid) < 1:
		return ''
	vid = vid[0]
	headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.1; Pixel Build/NMF26O) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.91 Mobile Safari/537.36',
	   'Origin': 'https://www.dailymotion.com',
	   'Referer': 'https://www.dailymotion.com/'}
	cookie = {'lang': 'en_US', 'ff': 'off'}
	session = GetSession()
	content = OpenURL("https://www.dailymotion.com/player/metadata/video/{0}".format(vid), session=session, headers=headers, cookies=cookie, responseMethod='json')
	if content.get('error') is not None:
		return ''
	else:
		cc = content['qualities']
		cc = list(cc.items())
		cc = sorted(cc, key=s, reverse=True)
		for source, json_source in cc:
			for item in json_source:
				m_url = item.get('url', None)
				if m_url:
					m_url = m_url.replace('dvr=true&', '')
					if '.m3u8?sec' in m_url:
						text = OpenURL(m_url, headers=headers, cookies=session.cookies.get_dict())
						mb = re.findall('NAME="([^"]+)"\n(.+)', text)
						mb = sorted(mb, key=s, reverse=True)
						for quality, strurl in mb:
							quality = quality.split("@")[0]
							if not strurl.startswith('http'):
								strurl1 = re.findall('(.+/)', m_url)[0]
								strurl = strurl1 + strurl
							strurl = '{0}|{1}'.format(strurl.split('#cell')[0], urlencode(headers))
							return strurl

def GetYouTube(url):
	if url.endswith('/'):
		url = url[:-1]
	video_id = url[url.rfind('/')+1:]
	if '?' in video_id:
		video_id = video_id[:video_id.find('?')]
	return '{0}/play/?video_id={1}'.format(youtubePlugin, video_id)
													   
def GetCF(url, ua=None, retries=10, responseMethod='text'):
	import resources.lib.cloudscraper as cloudscraper
	for i in range(retries):
		try:
			scraper = cloudscraper.create_scraper(interpreter = 'native')
			response = scraper.request('get', url)
			if response.status_code == 403:
				xbmc.sleep(1000)
				xbmc.log('{0}  -  response {1}.'.format(url, response.status_code), 3)
				continue
			if responseMethod == 'json':
				return response.json()
			elif responseMethod == 'full':
				return response
			else:
				return response.text
		except Exception as ex:
			xbmc.log(str(ex), 3)
			return None
	return ''

def GetCFheaders(url, ua=None, retries=10):
	import resources.lib.cloudscraper as cloudscraper
	for i in range(retries):
		try:
			scraper = cloudscraper.create_scraper(interpreter = 'native')
			response = scraper.request('get', url)
			if response.status_code == 403:
				xbmc.sleep(1000)
				xbmc.log('{0}  -  response {1}.'.format(url, response.status_code), 3)
				continue
			return response.headers
		except Exception as ex:
			xbmc.log(str(ex), 3)
			#return None
	return ''

def SaveImage(logoUrl, logoFile):
	try:
		if not os.path.isfile(logoFile):
			import threading
			threading.Thread(target=GetImageLinkBackground, args=(logoUrl, logoFile, )).start()
	except Exception as ex:
		xbmc.log("{0}".format(ex), 3)
	
def GetImageLinkBackground(logoUrl, logoFile):
	response = GetCF(logoUrl, responseMethod='full')
	if response.status_code == 200:
		with open(logoFile, 'wb') as f:
			for chunk in response:
				f.write(chunk)

def slugify(value, allow_unicode=False):
	import unicodedata
	value = str(value)
	if allow_unicode:
		value = unicodedata.normalize('NFKC', value)
	else:
		value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
	value = re.sub(r'[^\w\s-]', '', value.lower())
	return re.sub(r'[-\s]+', '-', value).strip('-_')