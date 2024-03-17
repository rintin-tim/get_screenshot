from get_screenshot import screenshot_db
from get_screenshot import screenshot, jinja_template, email_screenshot
from get_screenshot import flask_server
import datetime


def complete_summary(timestampid, email_list=None):
    try:
        screenshot_db.ScreenshotDB().set_summary_complete_status(timestampid, True)

    except Exception as err:
        print("something went wrong in completing status")

    try:
        web_html = jinja_template.generate_html(timestampid, save_to_db=True,
                                                save_to_file=True)  # when all URLs complete, generate template

        print("force complete: web template complete")
        if email_list:
            email_html = jinja_template.generate_html(timestampid,
                                                      email_list=email_list)  # when all URLs complete, generate template
            print("force complete: email template complete")
            email_screenshot.send_screenshot_email(email_html, email_list)
            print("force complete: email sent")

    except Exception as err:
        message = "** Error generating template or email: {}".format(err)
        print(message)
        email_screenshot.send_screenshot_email(message, email_list)

    print("clearing end time for {}: {}".format(timestampid, datetime.datetime.now()))
