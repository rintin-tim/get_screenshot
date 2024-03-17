import time

from jinja2 import Environment, PackageLoader, select_autoescape
from get_screenshot.screenshot_db import ScreenshotDB
from get_screenshot.screenshot_result import ScreenshotUrlResult, Screenshot
import datetime
from get_screenshot import helper, form_data
import json
import get_screenshot.conversions as conversions
import requests


first_url = None


def generate_html(timestampid, email_list=None, save_to_db=False, save_to_file=False):
    """ generate template and save to the database for retrieval """

    try:
        if email_list:
            first_names = [address[:address.find("@")] for address in email_list if "@" in address]  # list of emails before the @ symbol
            email_part = ", ".join(first_names)
        else:
            email_part = None

        project_timestamp = str(timestampid)
        project_timestamp_rows = ScreenshotDB().get_project_urls(project_timestamp)
        response_rows = ScreenshotDB().get_response_rows(project_timestamp)

        # Figure out the failed URLs
        summary_row = ScreenshotDB().get_summary_row(project_timestamp)
        form_json = json.loads(summary_row["form_json"])
        form_urls = form_data.clean_web_list(form_json['websitelist'])  # original urls submitted via the form
        status_urls = ScreenshotDB().get_project_status_urls(timestampid)  # project urls with statuses and timestamps
        error_urls = [(status[1], status[2]) for status in status_urls if not status[2] == 2]  # project urls with errors converted to list of tuples [(www.example.com, 1), (www.example2.com, -1)]
        missing_form_urls = [(url, 0) for url in form_urls if url not in [status[1] for status in status_urls]]  # form urls that don't have project urls. converted into list of tuples with 0 status added to tuple
        all_failed_urls = error_urls + missing_form_urls  # missing form urls combined with error urls

        label = {
            "-1": "Browserstack error",
            "0": "Not received by Browserstack",
            "1": "Started",
            "2": "Sent"
        }

        labelled_fails = [(url[0], label[str(url[1])])for url in all_failed_urls]  # labels unique to screenshot results page

        project_result = []  # full list of screenshot results for each url in the project
        if response_rows:
            response_dict = {}  # placeholder for responses in responses table, refactored to use job_id as the key

            for item in response_rows:
                time.sleep(1)
                latest_bs_json = requests.get("https://www.browserstack.com/screenshots/{}.json".format(item["job_id"])).json()
                response_dict.update({item["job_id"]:
                    {
                        "json": latest_bs_json,
                        "url_qty_remaining": item["url_qty_remaining"],
                        "last_modified": item["last_modified"]
                    }
                })

            if not response_dict:
                print("no responses retrieved from database - response_dict empty")
                return None

            for row in project_timestamp_rows:
                try:
                    # for each response/url
                    result = ScreenshotUrlResult()
                    result.test_url = row["test_url"]
                    global first_url
                    if not first_url:
                        first_url = result.test_url
                    result.result_url = row["result_url"]
                    result.job_id = row["job_id"]
                    jr = response_dict[result.job_id]["json"]
                    result.mac_res = jr["mac_res"]  # if global none, add
                    result.win_res = jr["win_res"]
                    result.wait_time = jr["wait_time"]
                    result.orientation = jr["orientation"]
                    result.qty_remaining = response_dict[result.job_id]["url_qty_remaining"]
                    result.modified = response_dict[result.job_id]["last_modified"]

                    # for each screenshot in response
                    response_screenshots = jr["screenshots"]
                    result.screenshots = []
                    for screenshot in response_screenshots:
                        shot = Screenshot()
                        shot.browser = screenshot["browser"]
                        shot.browser_version = screenshot["browser_version"]
                        shot.os = screenshot["os"]
                        shot.os_version = screenshot["os_version"]
                        shot.device = screenshot["device"]
                        shot.image_url = screenshot["image_url"]
                        shot.thumb_url = screenshot["thumb_url"]
                        shot.id = screenshot["id"]
                        shot.created_at = screenshot["created_at"]
                        result.screenshots.append(shot)  # add screenshot to list kept in ScreenshotResult
                    project_result.append(result)

                except KeyError as err:
                    print("that id is not ready yet: {}".format(err))
                    continue
                except Exception as err:
                    print("some other project_timestamp_row error: {}".format(err))
                    continue

            def sort_by_modified(project_item):
                """returns the modified date for a result object"""
                return project_item.modified

            project_result.sort(key=sort_by_modified)

        env = Environment(
            loader=PackageLoader('get_screenshot', 'templates'),
            autoescape=select_autoescape(['html', 'xml']),
        )

        def datetimeformat(value, format='%H:%M:%S (date: %d/%m/%Y)'):
            return value.strftime(format)

        def timeformat(value, format='%H:%M:%S'):
            return value.strftime(format)

        def removespaces(value: str):
            no_spaces = value.replace(" ", "")  # remove spaces
            no_dots = no_spaces.replace(".", "")  # remove dots
            return no_dots

        def formatlabel(value: str):
            if len(value) <= 3:
                title_case = value.upper()
            else:
                title_case = value.title()
            return title_case

        env.filters['titlelabel'] = formatlabel
        env.filters['datetimeformat'] = datetimeformat
        env.filters['timeformat'] = timeformat
        env.filters['removespaces'] = removespaces

        # return the email HTML if an email has been provided to the function
        if email_list:
            template = env.get_template('screenshot_email_template.html')
        else:
            template = env.get_template('results.html')

        summary = ScreenshotDB().get_summary_row(timestampid)

        # New project complete
        total_url_number = summary["url_qty"]

        current_url_number = len(project_result)
        unique_device = set()  # allows unique values only
        unique_browser = set()
        unique_os = set()

        for result in project_result:
            for shot in result.screenshots:
                if shot.device:
                    unique_device.add(shot.device)
                if shot.browser:
                    unique_browser.add(shot.browser)
                if shot.os:
                    unique_os.add(shot.os)

        # if project_result:
        project_complete = summary["project_complete"]  # if there's a mismatch in totals, use the value in summary to determine project status
        start_times = [item.modified for item in project_result]  # start time (modified) for each url

        # updated version
        average_delta = 0
        if start_times:
            earliest_time = min(start_times)
            latest_time = max(start_times)

            total_time_in_seconds = (latest_time - earliest_time).seconds
            print("earliest: {}| latest: {}| total: {}".format(earliest_time, latest_time, total_time_in_seconds))

            try:
                average_seconds = total_time_in_seconds / len(start_times)
                print("average seconds: {} from {} times in the list".format(average_seconds, start_times))
            except ZeroDivisionError:
                print("zero division error - average time set to zero")
                average_seconds = 0

            average_delta = helper.diffformat(average_seconds)

        html = template.render(email_part=email_part, results=project_result, current_number=current_url_number, total_urls=total_url_number,
                               project_complete=project_complete, timestampid=project_timestamp, average_delta=average_delta,
                               summary=summary, failed_urls=labelled_fails,
                               browser_filter=unique_browser, device_filter=unique_device, os_filter=unique_os)

        if save_to_file:
            helper.write_to_file(html)

        if save_to_db:  # if this is a web template, save it to the database
            ScreenshotDB().update_summary_with_html(timestampid, html)

        return html

    except Exception as err:
        raise


def generate_start_html(summary, summary_status):
    """ generate the html at the start of the process (after submission) """
    project_timestamp = summary["project_timestamp"]
    form_json = json.loads(summary["form_json"])

    browsers = form_data.get_browser_list(form_json)
    wait_time = form_json["waittime"]
    mac_res = form_json["macres"]
    win_res = form_json["winres"]
    form_urls = form_data.clean_web_list(form_json['websitelist'])  # original urls submitted via the form

    project_urls = ScreenshotDB().get_project_status_urls(project_timestamp)

    label = {
        "-1": "Error",
        "0": "Not started",
        "1": "Started",
        "2": "Sent"
    }

    url_statuses = []
    # get each url from form urls and find its corresponding status in the project table
    for form_url in form_urls:
        url_status = 0
        result_url = None
        for project in project_urls:
            if form_url == project["test_url"]:
                if project["status"]:
                    url_status = project["status"]
                if project["result_url"]:
                    result_url = project["result_url"]
        url_statuses.append((form_url, label[str(url_status)], result_url))

    project_complete = summary["project_complete"]

    env = Environment(
        loader=PackageLoader('get_screenshot', 'templates'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    def datetimeformat(value, format='%H:%M:%S (date: %d/%m/%Y)'):
        value = conversions.to_london_time(value)
        return value.strftime(format)

    def timeformat(value, format='%H:%M:%S'):
        value = conversions.to_london_time(value)
        return value.strftime(format)

    env.filters['datetimeformat'] = datetimeformat
    env.filters['timeformat'] = timeformat

    template = env.get_template('details.html')

    html = template.render(browsers=browsers, wait_time=wait_time, mac_res=mac_res,
                           win_res=win_res, project_complete=project_complete,
                           timestampid=project_timestamp, form_urls=form_urls, status=summary_status, url_statuses=url_statuses)

    return html


def generate_summary_html():
    summary_rows = ScreenshotDB().get_summary_rows()

    env = Environment(
        loader=PackageLoader('get_screenshot', 'templates'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    def datetimeformat(value, format='%H:%M:%S (date: %d/%m/%Y)'):
        if value:
            return value.strftime(format)
        else:
            return None

    def timeformat(value, format='%H:%M:%S'):
        return value.strftime(format)

    def timestamp_to_datetime(timestamp):
        """convert timestamp to human date and time"""
        date_time_obj = datetime.datetime.fromtimestamp(int(timestamp))
        date_format = '%d/%m/%Y %H:%M:%S'
        human_date = datetimeformat(date_time_obj, date_format)
        return human_date

    def status_to_text(value):
        """ convert status in database to pending, on going, complete"""
        if value is True:
            return "Complete"
        elif value is False:
            return "Started"
        else:
            return "Not started"

    env.filters['datetimeformat'] = datetimeformat
    env.filters['timeformat'] = timeformat
    env.filters['ts_to_dt'] = timestamp_to_datetime
    env.filters['status_to_text'] = status_to_text

    template = env.get_template('all.html')

    html = template.render(summaries=summary_rows)

    return html


def generate_redis_jobs_html(redis_jobs_obj, job_count):
    env = Environment(
        loader=PackageLoader('get_screenshot', 'templates'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    template = env.get_template('queue.html')
    html = template.render(redis_jobs=redis_jobs_obj, job_count=job_count)

    return html


def information_page(title, message, submit_button=False, all_button=False, queue_button=False):
    """ generic template:
    buttons is a list of tuple pairs. The first item in the pair is the button text, the second is the relative destination (aka path)"
    e.g.  information_page(title="Test Title", message="Test Message", buttons=[("Go to queue", "/queue"), ("All Jobs", "/all")])
    """
    env = Environment(
        loader=PackageLoader('get_screenshot', 'templates'),
        autoescape=select_autoescape(['html', 'xml']),
    )

    template = env.get_template('info.html')

    button_details = {
        "submit": ("New Screenshots", "/"),
        "all": ("All Jobs", "/all"),
        "queue": ("Queue Management", "/queue")
    }

    button_list = []
    if submit_button:
        button_list.append(button_details["submit"])
    if all_button:
        button_list.append(button_details["all"])
    if queue_button:
        button_list.append(button_details["queue"])

    html = template.render(title=title, message=message, buttons=button_list)

    return html


if __name__ == "__main__":
    information_page(title="Test Title", message="Test Message", submit_button=True)
