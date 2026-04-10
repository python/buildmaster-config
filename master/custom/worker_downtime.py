from datetime import datetime, timedelta


def no_builds_between(start, end, *, day_of_week=None, tz=None):
    """A function for "builder.canStartBuild" that implements planned downtime

    Avoid a build to be started between start and end time and delay such
    builds until end time.
    """

    start = datetime.strptime(start, "%H:%M").time()
    end = datetime.strptime(end, "%H:%M").time()
    def canStartBuild(builder, wfb, request):
        now_dt = datetime.now(tz=tz)
        if day_of_week is not None and now_dt.weekday() != day_of_week:
            return True
        now = now_dt.time()
        if is_within_time_range(now, start, end):
            delay = get_delay(now, end)
            # Adapted from: https://docs.buildbot.net/current/manual/customization.html#canstartbuild-functions
            wfb.worker.quarantine_timeout = delay
            wfb.worker.putInQuarantine()
            # This does not take the worker out of quarantine, it only resets
            # the timeout value to default (restarting the default
            # exponential backoff)
            wfb.worker.resetQuarantine()
            return False
        # Schedule the build now
        return True
    return canStartBuild

def is_within_time_range(now, start, end):
    if start <= end:
        return start <= now <= end
    else:
        return now >= start or now <= end


def get_delay(now, end):
    today = datetime.today()
    now = datetime.combine(today, now)
    end = datetime.combine(today, end)

    if now > end:
        end += timedelta(days=1)

    difference = end - now
    return difference.total_seconds()
