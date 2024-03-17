import os
import requests
import time
import datetime
from get_screenshot import screenshot_db
from get_screenshot.form_data import get_browser_list
from get_screenshot import flask_functions
from get_screenshot import redis_helper
from get_screenshot.status_check import StatusCheck
import rq.timeouts as timeouts

CALLBACK_ID = None


def bs_screenshot_request(CALLBACK_ID, url, form_data):
    callback_url = "https://getscreenshot.herokuapp.com/cb-screenshot/" + str(CALLBACK_ID)
    print("bs screenshot request: URL {}, callback URL: {}".format(url, callback_url))

    r = requests.post("https://www.browserstack.com/screenshots", json={
        "url": url,
        "callback_url": callback_url,
        "win_res": form_data["winres"],
        "mac_res": form_data["macres"],
        "quality": form_data["imagequality"],
        "wait_time": form_data["waittime"],
        "orientation": form_data["orientation"],
        "browsers": get_browser_list(form_data)
    }, auth=(os.environ.get("BS_UN"), os.environ.get("BS_TOKEN")))

    return r


def do_screenshot(CALLBACK_ID, test_url, remaining_qty, form_data, retry=True):
    try:
        project_status = screenshot_db.ScreenshotDB().get_summary_project_complete_status(CALLBACK_ID)
        print("project_status check: ", project_status)
        if project_status:
            print("Project set to complete but continue anyway")

        result = bs_screenshot_request(CALLBACK_ID, test_url, form_data)
        print("*!*! do_screenshot result code: {}".format(result.status_code))

        if result.status_code == 200:
            print("remaining_qty: ", remaining_qty)
            print("Working on url: {} time: {}".format(test_url, datetime.datetime.now().time()))
            result_json = result.json()
            job_id = result_json["job_id"]

            result_url = result.url + "/" + job_id
            print("*** screenshot url {}\n".format(result_url))
            email_list = []

            for key in form_data:
                if key.startswith("emailaddress"):
                    if form_data[key]:
                        email_list.append(form_data[key])

            # if successful, insert into projects table
            print(result_json)

            screenshot_db.ScreenshotDB().insert_project_values(CALLBACK_ID, test_url, result_url, remaining_qty,
                                                               job_id=result_json["job_id"], email=email_list, status=1,
                                                               browserstack_id=result_json["job_id"])

            screenshot_db.ScreenshotDB().set_summary_complete_status(CALLBACK_ID,
                                                                     False)  # False == 'started but not finished'

            flask_functions.flask_screenshot(CALLBACK_ID, job_id=job_id)

            if remaining_qty == 0:
                print("sending status check to redis")
                redis_helper.send_to_redis(StatusCheck().check_job_status, (CALLBACK_ID, job_id),
                                           description=None)  # wait for the job to be finished

            return "ok", result_json

        elif result.status_code == 422 and "Parallel limit reached" in result.text:
            if not retry:  # first instance - return busy
                print("system is busy with an earlier request")
                return "busy", str(CALLBACK_ID)
            else:
                print("422: limit reached - trying")
                time.sleep(60)
                return do_screenshot(CALLBACK_ID, test_url, remaining_qty, form_data)

        else:
            print("** UNEXPECTED BROWSERSTACK RESPONSE. STATUS: {} TEXT: {}".format(result.status_code, result.text))
            error_message = (result.status_code, result.text)

    except timeouts.JobTimeoutException as err:
        print("** JOB TIMEOUT ERROR {}".format(err))
        error_message = (err)

    # If error from browserstack or a timeout from Redis
    print("Error status applied in project table")
    screenshot_db.ScreenshotDB().insert_project_values(CALLBACK_ID, test_url, None, remaining_qty,
                                                       job_id=None, email=None, status=-1, browserstack_id=None)

    if remaining_qty == 0:
        print("something went wrong with the final url - set to complete")
        screenshot_db.ScreenshotDB().set_summary_complete_status(CALLBACK_ID,
                                                                 True)  # if there's an error on the last url. set status to complete
        email_list = [form_data[key] for key in form_data if key.startswith("emailaddress")]
        print("force completion....")
        data = {
            "timestampid": CALLBACK_ID,
            "complete_status": True,
            "email_list": email_list
        }

        r = requests.post("http://getscreenshot.herokuapp.com/force-complete", json=data)

        print("force url json: ", data)
        print("force url response: ", r)

    else:
        pass

    return "error", error_message
