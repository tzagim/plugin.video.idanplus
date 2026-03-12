import xbmc
import common

channelID = u'ללא'
channels = None
is_startup_ch = common.Addon.getSettingBool("is_startup_ch")
is_startup_rd = common.Addon.getSettingBool("is_startup_rd")

if is_startup_ch:	
	channels = common.GetChannels('tv')
	channelID = common.Addon.getSettingString("startup_ch")
elif is_startup_rd:	
	channels = common.GetChannels('radio')
	channelID = common.Addon.getSettingString("startup_rd")

if channelID != u'ללא' and channels is not None:
	chanID = None
	for chID, ch in channels:
		if chID == channelID: 
			chanID = chID
			break
	if chanID is not None:
		autoplayCommand = 'PlayMedia(plugin://plugin.video.idanplus/?mode=5&url={0})'.format(channelID)
		xbmc.executebuiltin(autoplayCommand)

refreshCommand = 'RunPlugin(plugin://plugin.video.idanplus/?mode=7)'
xbmc.executebuiltin(refreshCommand)
xbmc.executebuiltin('AlarmClock(idanplus,{0},12:00:00,silent,loop)'.format(refreshCommand))