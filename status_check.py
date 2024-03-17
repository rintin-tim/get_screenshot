import requests
import time
import datetime
from dateutil import relativedelta
from get_screenshot import screenshot_db
import json


class StatusCheck:

    start_time = None
    force_complete = False

    def check_job_status(self, timestampid, job_id):
        print("starting job status check")
        bs_json = requests.get("https://www.browserstack.com/screenshots/{}.json".format(job_id)).json()

        print("current state: {}".format(bs_json["state"]))
        print("start time: ", self.start_time)

        if bs_json["state"] == "done" or self.force_complete:
            print("timestamp: {} job: {} is done according to the JSON".format(timestampid, job_id))
            self.start_time = None  # reset value
            summary_row = screenshot_db.ScreenshotDB().get_summary_row(timestampid)
            form_json = json.loads(summary_row["form_json"])
            email_list = [form_json[key] for key in form_json if key.startswith("emailaddress")]
            print("email list: {}".format(email_list))
            screenshot_db.ScreenshotDB().set_summary_complete_status(timestampid, True)  # set project to complete

            data = {
                "timestampid": timestampid,
                "complete_status": True,
                "email_list": email_list
            }
            r = requests.post("http://getscreenshot.herokuapp.com/force-complete", json=data)

            print("json set complete: ", data)
            print("json set complete response: ", r)

            self.force_complete = False  # reset flag
            return True

        elif bs_json["stopped"]:
            print("Browserstack stopped status is True - I've stopped looking. force_complete flag set to True")
            self.force_complete = True
            self.check_job_status(timestampid, job_id)
            # return False

        elif self.start_time:
            if self.start_time + relativedelta.relativedelta(minutes=+6) < datetime.datetime.now():
                print("done status not found within 6 minutes - I've stopped looking. force_complete flag set to True")
                self.force_complete = True
                self.check_job_status(timestampid, job_id)
                # return False
            else:
                print("within 5 mins - waiting 10s then checking again")
                time.sleep(10)
                self.check_job_status(timestampid, job_id)

        else:
            print("check job status - else statement")
            if not self.start_time:
                print("start_time set")
                self.start_time = datetime.datetime.now()
            print("check job status - not done yet - trying again")
            time.sleep(10)
            self.check_job_status(timestampid, job_id)

