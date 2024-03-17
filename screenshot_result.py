import datetime
import pytz


class ScreenshotUrlResult:

    def __init__(self):
        self.test_url = None
        self.result_url = None
        self.job_id = None
        self.mac_res = None
        self.win_res = None
        self.wait_time = None
        self.orientation = None
        self.screenshots = None
        self.qty_remaining = None
        self._modified = None


    @property
    def modified(self):
        return self._modified

    @modified.setter
    def modified(self, value):
        """ value is datetime object"""
        utc_aware = value.replace(tzinfo=pytz.UTC)  # add utc tz to datetime
        london_tz = pytz.timezone('Europe/London')  # create a instance of London tz
        london_time = utc_aware.astimezone(london_tz)  # convert utc date to london time
        self._modified = london_time


class Screenshot:

    def __init__(self):
        """ object for each screenshot in a url """
        self.id = None
        self.browser = None
        self.browser_version = None
        self.os = None
        self.os_version = None
        self.device = None
        self._image_url = None
        self._thumb_url = None
        self.created_at = None


    @property
    def thumb_url(self):
        return self._thumb_url

    @thumb_url.setter
    def thumb_url(self, url):
        if url:
            self._thumb_url = url
        else:
            self._thumb_url = "https://getscreenshot.herokuapp.com/static/question-mark.png"

    @property
    def image_url(self):
        return self._image_url + "?" + self.id

    @image_url.setter
    def image_url(self, url):
        if url:
            self._image_url = url
        else:
            self._image_url = "https://getscreenshot.herokuapp.com/static/error-large.gif"
