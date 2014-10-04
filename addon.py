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
sys.path.append(os.path.join(__addonpath__, "resources/lib/tvdb_login"))
import tvdb_api
import tvdbauthenticate

percentage_limit = int(__addon__.getSetting("percentage_limit"))
display_past_rating = str(__addon__.getSetting("get_previous"))
allow_past_rating = __addon__.getSetting("rate_if_previous")
tvdb_username = __addon__.getSetting("tvdb_username")
tvdb_password = __addon__.getSetting("tvdb_password")
tvdb = tvdbauthenticate.TVDB(tvdb_username, tvdb_password)
account_id = tvdb.get_user_id()

if (tvdb_username == ""):
    xbmc.executebuiltin('Notification(TVDB Rating,No username given!,5000)')
    sys.exit(1)
elif (tvdb_password == ""):
    xbmc.executebuiltin('Notification(TVDB Rating,No password given!,5000)')
    sys.exit(1)
elif (account_id == -1):
    xbmc.executebuiltin('Notification(TVDB Rating,Unable to get user account id,5000)')
    sys.exit(1)

rating_url = "http://thetvdb.com/api/User_Rating.php?accountid="


class myPlayer(xbmc.Player):

    def __init__(self, *args):
        pass

    def onPlayBackStarted(self):
        if xbmc.Player().isPlayingVideo():
            self.isTvShow = False
            self.total_time = xbmc.Player().getTotalTime()
            result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "season", "episode", "showtitle"], "playerid": 1 }, "id": "VideoGetItem"}')
            data = json.loads(result)
            video_type = data['result']['item']['type']
            if (video_type == 'episode'):
                self.show_name = data['result']['item']['showtitle']
                self.episode_title = data['result']['item']['title']
                self.episode = data['result']['item']['episode']
                self.season = data['result']['item']['season']
                self.isTvShow = True

    def onPlayBackStopped(self):
        if (((current_time / self.total_time) * 100 > percentage_limit) and self.isTvShow):
            self.rateItem()

    def onPlayBackEnded(self):
        if (self.isTvShow):
            self.rateItem()

    def rateItem(self):
        dialog = xbmcgui.Dialog()
        season = self.season
        episode = self.episode

        if (season < 10):
            season = "0" + str(season)
        if (episode < 10):
            episode = "0" + str(episode)

        t = tvdb_api.Tvdb(apikey='0F7BE09C80105D50')
        episode_data = t[self.show_name][self.season][self.episode]
        self.item_id = episode_data['id']

        if (display_past_rating == "true"):
            episode_url = "http://thetvdb.com/?tab=episode&seriesid=" + episode_data['seriesid'] + "&seasonid=" + episode_data['seasonid'] + "&id=" + episode_data['id']
            previous_rating = tvdb.get_user_rating(episode_url)
            was_rated = True
            if (previous_rating == -1):
                was_rated = False
            elif (allow_past_rating == "false"):
                return

        item_name = self.show_name + " - " + "S" + str(season) + "E" + str(episode) + " - " + "'" + self.episode_title +"'"
        if (display_past_rating == "true" and was_rated):
            rating = dialog.select('%s\n Previous rating: %s' % (item_name, previous_rating), ['No rating (clears previous)', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        else:
            rating = dialog.select('Select a rating for:\n%s' % item_name, ['No rating', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])

            if ((len(account_id) > 15) and (len(account_id) < 33)):
                url = str(rating_url + account_id + "&itemtype=episode&itemid=" + self.item_id + "&rating=" + str(rating))
                req = urllib2.Request(url)
                urllib2.urlopen(req)
            else:
                # Invalid length for tvdb account identifier
                pass


player = myPlayer()

while (not xbmc.abortRequested):
    if xbmc.Player().isPlayingVideo():
        global current_time
        current_time = xbmc.Player().getTime()
    xbmc.sleep(100)
