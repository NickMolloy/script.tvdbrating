import os
import sys
import urllib2
import json
import xbmc
import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon("script.tvdbrating")
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')
sys.path.append(os.path.join(__addonpath__, "resources/lib/tvdb_api"))

import tvdb_api


class myPlayer(xbmc.Player):
    account_id = __addon__.getSetting("tvdbaccountid")
    percentage_limit = int(__addon__.getSetting("percentage_limit"))

    def __init__(self, *args):
        pass

    def onPlayBackStarted(self):
        if xbmc.Player().isPlayingVideo():
            self.isTvShow = False
            self.total_time = xbmc.Player().getTotalTime()
            result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "season", "episode", "showtitle"], "playerid": 1 }, "id": "VideoGetItem"}')
            data = json.loads(result)
            test = data['result']['item']['type']
            xbmc.executebuiltin("Notification('Hello','Type: %s') % test")
            xbmc.executebuiltin("Notification('Title','Message')")
            if (test == 'episode'):
            	self.show_name = data['result']['item']['showtitle']
		self.episode = data['result']['item']['episode']
		self.season = data['result']['item']['season']
                self.isTvShow = True

    def onPlayBackStopped(self):
        if (((current_time / self.total_time) * 100 > self.percentage_limit) and self.isTvShow):
            self.rateItem()

    def onPlayBackEnded(self):
	if (self.isTvShow):
		self.rateItem()

    def rateItem(self):
	dialog = xbmcgui.Dialog()
        ret = dialog.select('Select a rating:', ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        rating = ret + 1

        t = tvdb_api.Tvdb()
        episode = t[self.show_name][self.season][self.episode]
        self.item_id = episode['id']

        url = str("http://thetvdb.com/api/User_Rating.php?accountid=" + self.account_id + "&itemtype=episode&itemid=" + self.item_id + "&rating=" + str(rating))
        req = urllib2.Request(url)
        urllib2.urlopen(req)


player = myPlayer()

while (not xbmc.abortRequested):
    if xbmc.Player().isPlayingVideo():
        global current_time
        current_time = xbmc.Player().getTime()
    xbmc.sleep(100)
