"""
Delete everything from the schedule
"""

def delete_all():
    """Remove all scheduled items"""
    import xmlrpclib
    import configuration as conf
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    schedule_list = client.schedule.listInProgressActions(key)
    for schedule_item in schedule_list:
        schedule_id_list = [schedule_item['id']]
        try:
            client.schedule.cancelActions(key, schedule_id_list)
        except:
            pass


if __name__ == "__main__":
    delete_all()
