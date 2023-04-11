import xbmc

refreshCommand = 'RunPlugin(plugin://plugin.video.idanplus/?mode=7)'
xbmc.executebuiltin(refreshCommand)
xbmc.executebuiltin('AlarmClock(idanplus,{0},12:00:00,silent,loop)'.format(refreshCommand))
