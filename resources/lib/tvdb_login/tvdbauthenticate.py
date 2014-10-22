import requests
import cookielib
from bs4 import BeautifulSoup
import re
import logging


class TVDB(object):
    jar = None

    def __init__(self, username, password):
        self.username = username
        self.password = password
        logging.basicConfig(filename='tvdbauthenticate.log', level=logging.DEBUG)

    def authenticate(self):
        auth_url = "http://thetvdb.com/index.php?tab=login"
        self.session = requests.session()

        header = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        form_data = {
            'username': self.username,
            'password': self.password,
            'function': 'Log In',
            'submit': 'Log In',
            'setcookie': 'on'
        }

        # Create CookieJar
        self.jar = cookielib.CookieJar()

        # Authenticate
        response = self.session.post(auth_url, data=form_data, headers=header, cookies=self.jar)

        if (response.status_code == 200):
            # All is good
            pass
        else:
            # Something went wrong
            logging.error("Failed to authenticate")
            raise FailedAuthentication()

        successful = False
        for cookie in response.cookies:
            if (cookie.name == "cookieid" or cookie.name == "cookiepass"):
                # Authenication was successful
                successful = True
                logging.info("Successfully authenticated")
                break

        if (not(successful)):
            logging.error("Failed to authenticate")
            # Throw exception
            raise FailedAuthentication()

    # TODO must handle invalid urls (catch exceptions ?)
    def get_user_rating(self, url):
        logging.info("Attempting to get rating with URL: " + url)
        # Check if we have authenticated
        if (self.jar is None):
            # Haven't authenticated, should do it
            self.authenticate()

        rating = None

        # Attempt to parse TVDB page for user's rating
        response = self.session.get(url, cookies=self.jar)
        soup = BeautifulSoup(response.text)
        pattern = re.compile('(.*)(onmouseout=\"UserRating\()(\d)(.*)')

        for link in soup.find_all('a'):
            try:
                match = pattern.match(str(link))
                rating = match.group(3)
                break
            except:
                pass

        # Return result
        if (rating is None):
            logging.info("Unable to get rating")
            return -1
        else:
            logging.info("Got rating: " + rating)
            return int(rating)

    def get_user_id(self):
        account_url = "http://thetvdb.com/?tab=userinfo"
        logging.info("Attempting to get user account id")
        # Check if we have authenticated
        if (self.jar is None):
            # Haven't authenticated, should do it
            self.authenticate()

        account_id = None

        # Attempt to parse user's account page to get their id
        response = self.session.get(account_url, cookies=self.jar)
        soup = BeautifulSoup(response.text)
        pattern = re.compile('(<input name="form_uniqueid" readonly="" type="text" value=")(\w+)(".*)')

        for link in soup.find_all('input'):
            try:
                match = pattern.match(str(link))
                account_id = match.group(2)
                break
            except:
                pass

        if (account_id == None):
            # Couldn't get id
            logging.error("Couldn't get user account id")
            return -1
        else:
            logging.info("Successfully got id: " + account_id)
            return account_id

class FailedAuthentication(Exception):

    def __init__(self):
        super(FailedAuthentication, self).__init__()