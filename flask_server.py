from flask import Flask
from flask import request as frequest

import os
from flask import render_template

from get_screenshot import screenshot_db, jinja_template, quickshot, redis_helper
from get_screenshot import timestamp_complete
import datetime
from get_screenshot import flask_functions
import traceback


app = Flask(__name__)


def run_flask():
    port = int(os.environ.get('PORT', 5000))

    try:
        print("starting flask server")
        app.run(debug=True, host='0.0.0.0', port=port)

    except OSError:
        print("flask server already running")
        app.run(debug=True, host='0.0.0.0', port=port)


url_list = []
last_url = ""


@app.route('/force-complete', methods=['POST'])
def force_complete():
    data = frequest.get_json()
    screenshot(timestampid=data["timestampid"], complete_status=data["complete_status"], email_list=data["email_list"])
    print("force complete completed")
    return "force complete was completed for {}".format(data["timestampid"])


@app.route('/cb-screenshot/<timestampid>', methods=['POST'])
def screenshot(timestampid, complete_status=False, email_list=None, job_id=None):
    """callbacks received from browserstack"""
    return_statement = flask_functions.flask_screenshot(timestampid, complete_status, email_list, job_id)
    return return_statement


@app.route('/complete/<timestampid>', methods=['GET'])
def complete(timestampid):
    print("complete result request received for {}".format(timestampid))
    try:
        html = screenshot_db.ScreenshotDB().get_summary_html(timestampid)
        if not html:
            err_message = "** No completed HTML could be found in the database. Try /results version."
            print(err_message)
            return err_message, 404
        else:
            return html, 200
    except TypeError as err:
        err_message = "** No completed HTML could be found in the database. Try /results version. Error message: {}".format(str(err))
        print(err_message)
        return err_message, 404
    except Exception as err:
        err_message = "** Error encountered when returning html. Type: {}. Message: {}".format(type(err), str(err))
        print(err_message)
        return err_message, 500


@app.route('/details/<timestampid>')
def details(timestampid):
    try:
        summary_result = screenshot_db.ScreenshotDB().get_summary_row(timestampid)
        html = jinja_template.generate_start_html(summary_result, "details")
        if html:
            return html, 200
    except Exception as err:
        print("could not retrieve timestamp: {}. The stack trace is below:".format(err))
        traceback.print_exc()
        pass

    return jinja_template.information_page(title="Hmmm. You've screenshot-ed yourself in the foot :)",
                                           message="These results could not be found. They may have been deleted.",
                                           submit_button=True)


@app.route('/now/<timestampid>', methods=['GET'])
@app.route('/results/<timestampid>', methods=['GET'])
def now_template(timestampid):
    """ return the result based on the most recent html"""
    print("return timestamp {} in the current html template".format(timestampid))
    try:
        if timestampid and not timestampid == "None":
            summary_result = screenshot_db.ScreenshotDB().get_summary_row(timestampid)
            if not summary_result:  # ok
                return jinja_template.information_page(title="Hmmm. You've screenshot-ed yourself in the foot :)",
                                               message="These results could not be found. They may have been deleted.",
                                               submit_button=True)

            if summary_result["project_complete"] is None:  # exists but not started / status not known

                html = jinja_template.generate_html(timestampid)
                if not html:
                    html = jinja_template.generate_start_html(summary_result, "busy")
                return html, 200
            elif summary_result["project_complete"] is False:  # underway
                html = jinja_template.generate_html(timestampid)
                if not html:
                    html = jinja_template.generate_start_html(summary_result, "ok")
                return html, 200
            else:  # project complete
                html = jinja_template.generate_html(timestampid)
                if not html:
                    html = "Sorry, no page available yet. Try again in a few minutes"
                return html, 200

        else:
            return "extra request for unknown reason", 500
    except Exception as err:
        traceback.print_exc()
        return jinja_template.information_page(title="Hmmm. You've screenshot-ed yourself in the foot :)",
                                               message="These results could not be found. They may have been deleted.",
                                               submit_button=True)


@app.route('/submit', methods=['POST', 'GET'])
def submit():
    form_data = frequest.form
    print("##### START ######")
    print("form data: ", form_data)

    result = quickshot.main(form_data)

    status = result["status"]
    first_run_response = result["first_run_response"]
    summary = result["summary"]
    html = jinja_template.generate_start_html(summary, status)

    if not status == "error":
        return html
    else:
        return jinja_template.information_page(title="Hmmm. You've screenshot-ed yourself in the foot :)",
                                               message="Error encountered on first url: {}. Use the browser back button to correct your mistake.".format(first_run_response),
                                               )


@app.route('/', methods=['GET'])
def home():
    return render_template('submit.html')


def complete_timestamps():
    pass


@app.route('/clear-jobs', methods=['GET'])
def clear_redis():
    deleted_jobs = redis_helper.clear_redis_jobs()
    if (deleted_jobs[0] == 1) or (deleted_jobs[0] == 0 and deleted_jobs[1] == 0):
        return jinja_template.information_page(title="No jobs left to delete",
                                               message="It's happening",
                                               submit_button=True, all_button=True)
    else:
        active_timestamps = screenshot_db.ScreenshotDB().get_incomplete_timestamps()
        print("active timestamps: {}".format(active_timestamps))

        if active_timestamps:
            print("clearing redis start time: {}".format(datetime.datetime.now()))

            screenshot_db.ScreenshotDB().set_summary_complete_status(active_timestamps, True)

            for timestamp in active_timestamps:  # force completion actions after deletion of queue
                redis_helper.send_summary_to_redis(timestamp_complete.complete_summary, (timestamp,))
                return jinja_template.information_page(title="All jobs deleted",
                                                       message="There were {} but now it's zero. So... yeah.... that's that.".format(deleted_jobs[1]),
                                                       submit_button=True, all_button=True)

        else:
            return jinja_template.information_page(title="All projects have already been completed",
                                                   message="There's nothing left to do",
                                                   submit_button=True, all_button=True)


@app.route('/clear-jobs/id/<job_id>', methods=['GET'])
def remove_job_by_id(job_id):
    redis_helper.cancel_redis_job(job_id)
    return jinja_template.information_page(title="The requested url has been cleared.",
                                           message="There are {} jobs left in the queue.".format(
                                               redis_helper.count_redis_jobs()), all_button=True, queue_button=True)


@app.route('/clear-jobs/<timestamp>', methods=['GET'])
def remove_job_by_timestamp(timestamp):
    result = redis_helper.delete_all_timestamp_jobs(timestamp)
    if result[0] == 0:
        screenshot_db.ScreenshotDB().set_summary_complete_status(timestamp, True)
        return jinja_template.information_page(title="{} jobs will be deleted for the timestamp '{}'. ".format(result[1], timestamp),
                                               message="It may take a few minutes for this to be updated.",
                                               all_button=True, queue_button=True)
    else:
        return jinja_template.information_page(
            title="Try again - an error was encountered",
            message="{} jobs for the timestamp {} have been cleared. Error message {}.".format(result[1], timestamp, result[2]),
            all_button=True, queue_button=True)


@app.route('/queue')
def jobs_in_queue():
    redis_jobs = redis_helper.get_redis_job_details()
    print("jobs in queue - redis jobs", redis_jobs)

    count = 0
    for timestamp in redis_jobs:
        try:
            for job in redis_jobs[timestamp]:
                count += 1
        except TypeError:
                print("type error averted")

    try:
        html = jinja_template.generate_redis_jobs_html(redis_jobs, count)
        if html:
            return html
    except Exception as err:
        traceback.print_exc()
        pass

    return jinja_template.information_page(
            title="No Jobs found:",
            message="So there's nothing to do here",
            all_button=True, queue_button=True)


@app.route('/all')
def project_summary():
    """ return summary """
    html = jinja_template.generate_summary_html()
    return html


if __name__ == "__main__":
    run_flask()

