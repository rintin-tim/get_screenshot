import requests
import json
from get_screenshot import screenshot_db, jinja_template, email_screenshot


def flask_screenshot(timestampid, complete_status=False, email_list=None, job_id=None):
    """
    gets the json result from browserstack for the job id.
    updates project complete.
    triggers the email send if project complete"""

    if job_id:
        bs_json = requests.get("https://www.browserstack.com/screenshots/{}.json".format(job_id)).json()
        print("response fetched from browserstack for {}".format(bs_json["screenshots"][0]["url"]))
        screenshot_db.ScreenshotDB().insert_response_values(timestampid, bs_json)  # add to 'responses' table

    screenshot_db.ScreenshotDB().set_summary_complete_status(timestampid, complete_status)

    if complete_status:
        try:
            if email_list:
                email_html = jinja_template.generate_html(timestampid, email_list=email_list)  # when all URLs complete, generate template
                email_screenshot.send_screenshot_email(email_html, email_list)
        except Exception as err:
            message = "** Error generating template or email: {}".format(err)
            print(message)
            email_screenshot.send_screenshot_email(message, email_list)

    return "<h1>Success was achieved. Good for you</h1>", 200
