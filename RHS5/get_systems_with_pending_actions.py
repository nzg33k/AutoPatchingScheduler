"""
Get a count of actions pending
"""


def find_pending_action_count():
    """"Look for systems with a specific package installed"""
    import configuration as conf
    import xmlrpclib
    import datetime
    now = datetime.datetime.now()
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    actions = client.schedule.listInProgressActions(key)
    pending_action_count = 0

    for action in actions:
        """Only count future actions, not ones that are pending"""
        if action['earliest'] > now:
            pending_action_count += 1
    print pending_action_count


def find_sys_with_pending_actions(show_progress=True, show_time=True):
    """Rather that a straight count of actions, get a count of systems with actions.  More complex, but more useful."""
    import configuration as conf
    import xmlrpclib
    import sys
    import datetime
    now = datetime.datetime.now()
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    system_list = set()
    systems_processed = 0
    actions = client.schedule.listInProgressActions(key)

    if show_time:
        print "Started at: " + str(datetime.datetime.now())

    for action in actions:
        """Only count future actions, not ones that could run now"""
        if action['earliest'] > now:
            systems = client.schedule.listInProgressSystems(key, action['id'])
            for system in systems:
                system_list.add(system['server_id'])
                if show_progress:
                    systems_processed += 1
                    sys.stdout.write('\r' + str(systems_processed))

    if show_time:
        print "Finished at: " + str(datetime.datetime.now())
    print "Unique systems with actions pending: " + str(len(system_list))


if __name__ == "__main__":
    find_sys_with_pending_actions()
