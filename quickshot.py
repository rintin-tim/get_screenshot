import datetime
from get_screenshot import screenshot_db

from get_screenshot.redis_helper import send_to_redis
from get_screenshot.screenshot import do_screenshot
from get_screenshot import redis_helper
from get_screenshot.form_data import clean_web_list
import json

CALLBACK_ID = None


def get_timestamp():
    # TODO can be deleted
    """generate the id to use (timestamp)"""
    ts = datetime.datetime.now().timestamp()
    return ts


def main(form_data=None):
    global CALLBACK_ID

    date_time_now = datetime.datetime.now()
    CALLBACK_ID = str(int(date_time_now.timestamp()))

    first_run_response = None
    status = None
    existing_job_descriptions = None

    current_url_list = clean_web_list(form_data["websitelist"])
    combination_qty = len([key for key in form_data if key.startswith("combi_")])

    # update summary
    screenshot_db.ScreenshotDB().insert_summary_values(CALLBACK_ID, current_url_list[0], len(current_url_list), json.dumps(form_data), project_complete=None, created_at=date_time_now, combination_qty=combination_qty)

    for index, url in enumerate(current_url_list):
        print(" **** " + str(index))
        urls_remaining = len(current_url_list) - (index + 1)

        if index == 0:
            # try to run, if it's busy then do it through redis.
            status, first_run_response = do_screenshot(CALLBACK_ID, url, urls_remaining, form_data, retry=False)

            if status == "busy":
                print("busy at the moment - sending to redis")
                existing_job_descriptions = redis_helper.get_redis_job_details()
                existing_job_descriptions = "# Jobs: {}. # URLs: {}".format(len(existing_job_descriptions), existing_job_descriptions)
                send_to_redis(do_screenshot, (CALLBACK_ID, url, urls_remaining, form_data))
            if status == "error":
                print("some other kind of error - not sending to redis")
                break  # don't send anything to redis
        else:
            result = send_to_redis(do_screenshot, (CALLBACK_ID, url, urls_remaining, form_data))
            print("redis result: {}".format(result))

    print(CALLBACK_ID)
    print(first_run_response)

    summary = screenshot_db.ScreenshotDB().get_summary_row(CALLBACK_ID)

    result_obj = {
        "status": status,
        "first_run_response": first_run_response,
        "existing_job_descriptions": existing_job_descriptions,
        "form_values": json.loads(summary["form_json"]),
        "project_timestamp": summary["project_timestamp"],
        "summary": summary

    }

    return result_obj


if __name__ == "__main__":
    main()

