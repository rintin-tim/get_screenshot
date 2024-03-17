import psycopg2
import os
import json
from psycopg2.extras import DictCursor
from flask import request as frequest
# import get_screenshot.jinja_template as jinja_template
from ast import literal_eval


class ScreenshotDB:

    def connect_to_database(self):

        DATABASE_URL = os.environ['DATABASE_URL']  # for live
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor, sslmode='require')

        return conn

    def insert_response_values(self, timestampid, bs_json):
        """ insert the values returned from browser to the database. update project urls with status """

        s_timestamp = timestampid
        job_id = bs_json['id']
        status = "complete"
        json_response = json.dumps(bs_json)
        test_url = bs_json["screenshots"][0]["url"]  # include this in a separate id table along with number of urls
        win_resolution = bs_json["win_res"]
        mac_resolution = bs_json["mac_res"]
        wait_time = bs_json["wait_time"]
        last_update = None

        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO responses (timestamp, job_id, json_response, test_url, win_resolution, mac_resolution, wait_time, last_update) VALUES (%s, %s, %s, %s, %s, %s, %s, now())",
        (s_timestamp, job_id, json_response, test_url, win_resolution, mac_resolution, wait_time))

        cursor.execute("UPDATE projects SET status = 2 WHERE CAST(project_timestamp AS INTEGER)= %s AND job_id LIKE %s", (timestampid, job_id, ))
        conn.commit()

        cursor.close()
        conn.close()

    def insert_project_values(self, timestampid, test_url, result_url, remaining_qty, job_id=None, email=None, status=0, browserstack_id=None):

        project_timestamp = timestampid
        test_url = test_url

        conn = self.connect_to_database()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO projects (project_timestamp, url_qty_remaining, test_url, result_url, last_modified, job_id, email, status, browserstack_id) VALUES (%s, %s, %s, %s, now(), %s, %s, %s, %s)", (project_timestamp, remaining_qty, test_url, result_url, job_id, email, status, browserstack_id))

        conn.commit()

        cursor.close()
        conn.close()

    def is_project_complete(self, timestampid, job_id=None):
        """ check if a 'url remaining 0' exists for this project timestamp. if it does return true. get the emails
        addresses to send the notification to """

        conn = self.connect_to_database()
        cursor = conn.cursor()

        # TODO if no job_id provided - alter SQL statement to remove job_id
        if job_id is None:
            cursor.execute(
                "SELECT url_qty_remaining, email FROM projects WHERE Cast(project_timestamp AS INTEGER)=%s",
                (timestampid,))
        else:
            cursor.execute(
                "SELECT url_qty_remaining, email FROM projects WHERE Cast(project_timestamp AS INTEGER)=%s AND job_id=%s",
                (timestampid, job_id))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        status_complete = False
        email_addresses = []

        for row in rows:
            if row["url_qty_remaining"] == 0: 
                print(row)
                print("**** PROJECT COMPLETE!!! PROJECT TIMESTAMP: {} ****".format(timestampid))
                status_complete = True
                emails = row["email"]
                if emails:
                    email_addresses = emails.strip("{}").split(",")

        return status_complete, email_addresses


    def set_summary_complete_status(self, timestampid, status: bool):
        """ update the summary table with 'complete' status (or not) when complete (or not).
        timestampid can be a list, tuple or str. the function will convert it to a tuple """

        if type(timestampid) == str:
            timestampid = tuple(timestampid.split(","))  # convert single value string to tuple
        elif type(timestampid) == list:
            timestampid = tuple(timestampid)  # convert a list to a tuple
        elif type(timestampid) is not tuple:
            raise Exception("Not a string, list or tuple")  # convert tim

        print("setting summary status to {} for timestamps {}".format(status, timestampid))
        conn = self.connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE summary SET project_complete = %s WHERE Cast(project_timestamp AS INTEGER) IN %s AND project_complete IS NOT true",
            (status, timestampid,))

        conn.commit()
        cursor.close()
        conn.close()

        return len(timestampid)  # number of timestamps set to complete

    def get_project_urls(self, timestampid):
        """ return all rows pertaining to a timestamp"""
        conn = self.connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT project_timestamp, test_url, result_url, job_id, status FROM projects WHERE Cast(project_timestamp AS INTEGER) = %s", (timestampid, ))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows

    def get_project_status_urls(self, timestampid):
        """ return all urls and statuses pertaining to a timestamp"""
        conn = self.connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT project_timestamp, test_url, status, result_url FROM projects WHERE Cast(project_timestamp AS INTEGER) = %s", (timestampid, ))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows

    def get_response_row(self, timestampid, jobid):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, json_response, job_id FROM responses WHERE Cast(timestamp AS INTEGER) = %s AND job_id = %s", (timestampid, jobid))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row

    def get_response_rows(self, timestampid):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT responses.timestamp, responses.json_response, responses.job_id, projects.url_qty_remaining, projects.last_modified FROM responses INNER JOIN projects on responses.job_id=projects.job_id where Cast(timestamp as INTEGER) = %s", (timestampid, )
        )

        row = cursor.fetchall()
        cursor.close()
        conn.close()

        return row


    def _insert_summary_values(self, timestampid, first_url, url_quantity, html):
        "update the summary table with the results"
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO summary (project_timestamp, first_url, url_qty, html) VALUES (%s, %s, %s, %s)", (timestampid, first_url, url_quantity, html))

        conn.commit()

        cursor.close()
        conn.close()

    def insert_summary_values(self, timestampid, first_url, url_quantity, form_json, project_complete, created_at, combination_qty):
        "update the summary table with the results"

        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO summary (project_timestamp, first_url, url_qty, form_json, project_complete, created_at, combi_qty) VALUES (%s, %s, %s, %s, %s, %s, %s)", (timestampid, first_url, url_quantity, form_json, project_complete, created_at, combination_qty))

        conn.commit()

        cursor.close()
        conn.close()

    def get_incomplete_timestamps(self):
        """ return the timestamps that are not completed """
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT project_timestamp FROM summary WHERE NOT project_complete = true OR project_complete IS NULL AND CAST(project_timestamp as INTEGER) > 1565709608;"
        )

        rows = cursor.fetchall()
    
        cursor.close()
        conn.close()

        timestamp_list = [row["project_timestamp"] for row in rows]

        return timestamp_list

    def update_summary_with_html(self, timestampid, html):
        """update the summary table with the results"""
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE summary SET html = %s WHERE Cast(project_timestamp AS INTEGER) = %s", (html, timestampid))

        conn.commit()

        cursor.close()
        conn.close()

    def get_summary_html(self, timestampid):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT html FROM summary WHERE Cast(project_timestamp AS INTEGER) = %s", (timestampid, ))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row[0]

    def get_summary_project_complete_status(self, timestampid):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT project_complete FROM summary WHERE Cast(project_timestamp AS INTEGER) = %s", (timestampid,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row[0]

    def get_summary_qty(self, timestampid):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url_qty FROM summary WHERE Cast(project_timestamp AS INTEGER) = %s", (timestampid,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row[0]

    def get_summary_row(self, timestampid):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM summary WHERE Cast(project_timestamp AS INTEGER) = %s", (timestampid,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row

    def get_summary_rows(self, number=None):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        if not number:
            cursor.execute(
                "SELECT id, project_timestamp, first_url, url_qty, project_complete, created_at, combi_qty FROM summary ORDER BY id DESC",)
        else:
            cursor.execute(
                "SELECT id, project_timestamp, first_url, url_qty, project_complete, created_at, combi_qty FROM summary ORDER BY id DESC LIMIT %s", (number,))

        row = cursor.fetchall()

        cursor.close()
        conn.close()

        return row

    def get_row_limit_timestamp(self, row_limit=4000):
        """get the newest timestamp to be deleted. i.e. the oldest timestamp after the most recent 4k"""

        print("Delete row limit: {}".format(row_limit))

        conn = self.connect_to_database()
        cursor = conn.cursor()

        # get the list of timestamps to be deleted with count of URLs
        cursor.execute(
            "SELECT DISTINCT project_timestamp, count(*) AS qty FROM (SELECT project_timestamp, ROW_NUMBER () OVER (ORDER BY id DESC) FROM projects) AS over_limit WHERE row_number > %s GROUP BY project_timestamp ORDER BY project_timestamp DESC",
            (row_limit,)
        )

        to_delete = cursor.fetchall()
        print("Row cleanup - Project timestamps over limit to be deleted: {}".format(["Timestamp: {} -> Count: {}".format(timestamp["project_timestamp"], timestamp["qty"]) for timestamp in to_delete]))

        # get the newest timestamp to be deleted from projects table
        cursor.execute(
            "SELECT MAX(DISTINCT project_timestamp) FROM (SELECT project_timestamp, ROW_NUMBER () OVER (ORDER BY id DESC) FROM projects) AS add_row_numbers WHERE row_number > %s",
            (row_limit,)
        )

        row = cursor.fetchone()
        max_timestamp = row[0]  # timestamp to delete

        print("newest timestamp over limit to be deleted: {}".format(max_timestamp))

        cursor.close()
        conn.close()

        return max_timestamp

    def cleanup_timestamp(self, cutoff_timestampid):
        """ remove timestamps older than the cutoff timestamp provided """

        print("run the timestamp cleanup function")

        conn = self.connect_to_database()
        cursor = conn.cursor()

        # get the rows counts to print to the console before deletion
        cursor.execute(
            'SELECT '
            '( SELECT COUNT(*) FROM projects where CAST(project_timestamp AS INTEGER) <= %s ) AS project_count,'
            '( SELECT COUNT(*) FROM responses where CAST(timestamp AS INTEGER) <= %s ) AS response_count,'
            '( SELECT COUNT(*) FROM summary where CAST(project_timestamp AS INTEGER) <= %s ) AS summary_count',
            (cutoff_timestampid, cutoff_timestampid, cutoff_timestampid)
        )

        result = cursor.fetchone()

        response_count = result["response_count"]
        project_count = result["project_count"]
        summary_count = result["summary_count"]

        print("Expected row counts for deletion: Summaries: {}. Projects: {}. Responses: {}. ".format(summary_count, project_count, response_count))

        # get the summary timestamp count for items to be deleted
        cursor.execute(

            'SELECT project_timestamp, url_qty  FROM summary where CAST(project_timestamp AS INTEGER) <= %s',
            (cutoff_timestampid,)
        )

        to_delete = cursor.fetchall()
        print("The following Summary timestamps will be deleted: {}".format(
            ["Timestamp: {} -> URL qty count: {}".format(timestamp["project_timestamp"], timestamp["url_qty"]) for timestamp in to_delete]))

        # get the list of timestamps to be deleted with ocunt of URLs
        cursor.execute("DELETE FROM projects where CAST(project_timestamp AS INTEGER) <= %s", (cutoff_timestampid,))
        project_rows_deleted = cursor.rowcount
        cursor.execute("DELETE FROM summary where CAST(project_timestamp AS INTEGER) <= %s", (cutoff_timestampid,))
        summary_rows_deleted = cursor.rowcount
        cursor.execute("DELETE FROM responses where CAST(timestamp AS INTEGER) <= %s", (cutoff_timestampid,))
        response_rows_deleted = cursor.rowcount

        print("Count of deleted rows (pre-commit)... Summary Rows: {}. Project Rows: {}. Response Rows: {}".format(summary_rows_deleted, project_rows_deleted, response_rows_deleted))

        conn.commit()
        cursor.close()
        conn.close()

        print("Rows deleted successfully (post-commit)")

        count_result = {
            "summary": summary_rows_deleted,
            "project": project_rows_deleted,
            "response": response_rows_deleted
        }

        return count_result

    def delete_timestamp(self, timestampid):

        """ remove specific timestamp. not implemented but still useful for maintenance... I think"""

        print("delete timestamp from database {}".format(timestampid))

        conn = self.connect_to_database()
        cursor = conn.cursor()

        # get the rows counts to print to the console before deletion
        cursor.execute(
            'SELECT '
            '( SELECT COUNT(*) FROM projects where CAST(project_timestamp AS INTEGER) = %s ) AS project_count,'
            '( SELECT COUNT(*) FROM responses where CAST(timestamp AS INTEGER) = %s ) AS response_count,'
            '( SELECT COUNT(*) FROM summary where CAST(project_timestamp AS INTEGER) = %s ) AS summary_count',
            (timestampid, timestampid, timestampid)
        )

        result = cursor.fetchone()

        response_count = result["response_count"]
        project_count = result["project_count"]
        summary_count = result["summary_count"]

        print("Expected row counts for deletion: Summaries: {}. Projects: {}. Responses: {}. ".format(summary_count,
                                                                                                      project_count,
                                                                                                      response_count))

        # get the list of timestamps to be deleted with ocunt of URLs
        cursor.execute("DELETE FROM projects where CAST(project_timestamp AS INTEGER) = %s", (timestampid,))
        project_rows_deleted = cursor.rowcount
        cursor.execute("DELETE FROM summary where CAST(project_timestamp AS INTEGER) = %s", (timestampid,))
        summary_rows_deleted = cursor.rowcount
        cursor.execute("DELETE FROM responses where CAST(timestamp AS INTEGER) = %s", (timestampid,))
        response_rows_deleted = cursor.rowcount

        print("Count of deleted rows (pre-commit)... Summary Rows: {}. Project Rows: {}. Response Rows: {}".format(
            summary_rows_deleted, project_rows_deleted, response_rows_deleted))

        conn.commit()
        cursor.close()
        conn.close()

        count_result = {
            "summary": summary_rows_deleted,
            "project": project_rows_deleted,
            "response": response_rows_deleted
        }

        return count_result

