"""
Look for systems with a specific package installed

RHS shows you systems that have packages it manages, but not so for packages it does not manage.
Whilst the system is known to have the package, the package is not known to be on the system.
This script will check every system for the given package.
"""


def find_sys_with_package(sought_package, show_progress=False):
    """"Look for systems with a specific package installed"""
    import configuration as conf
    import sys
    import xmlrpclib
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    systems = client.system.listSystems(key)

    hits = []
    for system in systems:
        progress_char = "."
        for package in client.system.listPackages(key, system['id']):
            if package['name'] == sought_package:
                hits.append(system['name'])
                progress_char = "+"
        if show_progress:
            sys.stdout.write(progress_char)
            sys.stdout.flush()
    return hits


def main():
    """"Use the arguments and call the function"""
    import sys
    if len(sys.argv) == 2:
        hits = find_sys_with_package(str(sys.argv[1]), True)
        print "\n"
        print "These systems have the package ", str(sys.argv[1])
        print hits
    else:
        print "Please provide one argument, the package to seek"


if __name__ == "__main__":
    main()
