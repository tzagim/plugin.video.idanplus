import xbmc
from time import time

end_pause = time() + 15
monitor = xbmc.Monitor()
wait_for_abort = monitor.waitForAbort

while not monitor.abortRequested():
    while time() < end_pause: wait_for_abort(1)
    refreshCommand = 'RunPlugin(plugin://plugin.video.idanplus/?mode=7)'
    xbmc.executebuiltin(refreshCommand)
    xbmc.executebuiltin('AlarmClock(idanplus,{0},12:00:00,silent,loop)'.format(refreshCommand))
    break