import xbmc
import common, baseChannels

startup_name = u'ללא'
channels = None
is_startup_ch = common.Addon.getSettingBool("is_startup_ch")
is_startup_rd = common.Addon.getSettingBool("is_startup_rd")

if is_startup_ch:	
	channels = baseChannels.TvChannels
	startup_name = common.Addon.getSettingString("startup_ch")
elif is_startup_rd:	
	channels = baseChannels.RadioChannels
	startup_name = common.Addon.getSettingString("startup_rd")

if startup_name != u'ללא' and channels is not None:
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