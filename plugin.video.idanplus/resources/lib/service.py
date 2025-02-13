import xbmc
import common, baseChannels

channels = None
startup_ch = common.GetAddonSetting("startup_ch")
startup_rd = common.GetAddonSetting("startup_rd")

if startup_ch != u'ללא':	
	channels = baseChannels.TvChannels
	startup_name = startup_ch
elif startup_rd != u'ללא':	
	channels = baseChannels.RadioChannels
	startup_name = startup_rd

if channels is not None:
	channel = None
	for ch in channels:
		if common.GetLocaleString(ch['nameID']) == startup_name: 
			channel = ch
			break
	if channel is not None:
		autoplayCommand = 'PlayMedia(plugin://plugin.video.idanplus/?mode=5&url={0})'.format(channel['ch'])
		xbmc.executebuiltin(autoplayCommand)

refreshCommand = 'RunPlugin(plugin://plugin.video.idanplus/?mode=7)'
xbmc.executebuiltin(refreshCommand)
xbmc.executebuiltin('AlarmClock(idanplus,{0},12:00:00,silent,loop)'.format(refreshCommand))