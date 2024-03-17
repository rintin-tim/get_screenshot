from rq import Queue
from rq import cancel_job
from worker import conn
from contextlib import contextmanager
from collections import namedtuple


@contextmanager
def redis_queue():
    try:
        q = Queue(connection=conn, )
        yield q
    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, message, str(err)


def count_redis_jobs():
    try:
        q = Queue(connection=conn, )
        jobs_count = q.count
        print("jobs count: {}".format(jobs_count))
        return jobs_count
    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, message, str(err)


def description_redis_jobs():
    try:
        q = Queue(connection=conn, )
        descriptions = [job.description for job in q.get_jobs()]
        print("job descriptions: {}".format(descriptions))
        return descriptions
        # jobs_count = q.count

    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, message, str(err)


def cancel_redis_job(job_id):
    try:
        cancel_job(job_id, conn)
        print("job deleted: {}".format(job_id))
        return True


    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, message, str(err)


def get_redis_job_details():
    """ specifically for screenshots """
    job_details = {}
    try:
        q = Queue(connection=conn, )
        job_objects = q.get_jobs()
        for job in job_objects:
            print("job details - job id: ", job.id)
            print("job details - job args: ", job.args)
            timestamp = job.args[0]
            url = job.args[1]
            remaining_qty = job.args[2]

            job_id = job.id
            created_date = job.created_at.strftime('%c')  # datetime object
            Description = namedtuple('desc', ['timestamp', 'url', 'remaining_qty', 'job_id', 'created_at'])
            desc = Description(timestamp, url, remaining_qty, job_id, created_date)

            if timestamp not in job_details:
                job_details.update({timestamp: [desc]})
            else:
                job_details[timestamp].append(desc)
        return job_details
    except Exception as err:
        print("redis connection error: ", str(err))
        print("An error occurred when trying to return redis job details...")
        return job_details


def clear_redis_jobs():
    try:
        q = Queue(connection=conn, )
        jobs_count = q.empty()
        print("jobs deleted: {}".format(jobs_count))
        return 0, jobs_count
    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to clear redis jobs..."
        return 1, message, str(err)


def send_to_redis(function, params, description=True, queue_name='default'):
    """ params: reminder - send multiple arguments for a function in a single tuple """
    description_config = (params[0], params[1], params[2]) if description else None
    try:
        q = Queue(name=queue_name, connection=conn, )
        result = q.enqueue(function, args=params, timeout=600, description=description_config, )
        print("sent to redis with params: {0}".format(description_config))
        return 0, result
    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, message, str(err)


def send_summary_to_redis(function, params):
    """ params: reminder - send multiple arguments for a function in a single tuple """
    try:
        q = Queue(connection=conn, )
        result = q.enqueue(function, args=params, timeout=600, description=(params[0],))
        print("send summary sent to redis with params: {0}".format(params))
        return 0, result
    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, message, str(err)


def delete_all_timestamp_jobs(timestamp):
    """ delete all pages/jobs for a given timestamp """

    delete_count = 0
    print("begin delete all for timestamp: {}".format(timestamp))
    try:
        q = Queue(connection=conn, )
        jobs = q.get_jobs()
        for job in jobs:
            if job.args[0] == timestamp:
                send_to_redis(cancel_redis_job, (job.id,), description=False, queue_name="high")
                delete_count += 1
        return 0, delete_count
    except Exception as err:
        print("redis connection error: ", str(err))
        message = "An error occurred when trying to complete this task..."
        return 1, delete_count, message, str(err)
