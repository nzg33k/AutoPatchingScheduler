"""
Look for systems with a specific package installed
"""


def find_sys_with_package(sought_package):
    """"Look for systems with a specific package installed"""
    from landscape_api.base import API as landscape_api
    # This file should be based on configuration.py.template
    import configuration as conf
    import pycurl
    api = landscape_api(conf.LDS_URI, conf.LDS_KEY, conf.LDS_SECRET, conf.LDS_CA)
    packages = api.get_packages(query="NOT tag:testapsw", names=sought_package)
    all_installed = set()
    hits = []
    for package in packages:
        installed = package['computers']['installed']
        if installed:
            for system in installed:
                all_installed.add(system)
    for system in all_installed:
        hits.append(api.get_computers(query="id:" + str(system))[0]['hostname'].encode("utf-8"))
    return hits


def main():
    """"Use the arguments and call the function"""
    import sys
    if len(sys.argv) == 2:
        hits = find_sys_with_package(str(sys.argv[1]))
        print "\n"
        print "These systems have the package ", str(sys.argv[1])
        print hits
    else:
        print "Please provide one argument, the package to seek"


if __name__ == "__main__":
    main()
