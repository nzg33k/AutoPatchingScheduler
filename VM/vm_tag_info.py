"""
More VMWare play
"""


# Require pyyaml and the Vsphere sdk
def chunks(mylist, max_length):
    """Break mylist into pieces no bigger than max_length"""
    result = []
    for i in range(0, len(mylist), max_length):
        working_length = i + max_length
        if len(mylist) < working_length:
            working_length = len(mylist)
        result.append(mylist[i:working_length])
    return result


def connect_vsphere():
    """Connect to Vsphere"""
    import configuration as config
    import requests
    import urllib3
    from vmware.vapi.vsphere.client import create_vsphere_client
    # Create a session object in the client.
    session = requests.Session()
    # We don't have valid certificates so...
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.verify = False
    vsphere_client = create_vsphere_client(
        server=config.VM_HOSTNAME,
        username=config.VM_USERNAME,
        password=config.VM_PASSWORD,
        session=session
    )
    return vsphere_client


def connect_cis():
    """Connect to CIS"""
    import configuration as config
    import requests
    import urllib3
    from vmware.vapi.security.user_password import create_user_password_security_context
    from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
    from vmware.vapi.lib.connect import get_requests_connector
    from vmware.vapi.security.session import create_session_security_context
    from com.vmware.cis_client import Session
    # Create a session object in the client.
    session = requests.Session()
    # We don't have valid certificates so...
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.verify = False
    # Create a connection for the session.
    connector = get_requests_connector(
        session=session,
        url='https://' + config.VM_HOSTNAME + '/api'
    )
    # Add username/password security context to the connector.
    connector.set_security_context(
        create_user_password_security_context(
            config.VM_USERNAME,
            config.VM_PASSWORD
        )
    )
    # Create a stub configuration by using the username-password security context.
    my_stub_config = StubConfigurationFactory.new_std_configuration(connector)
    # Create a Session stub with username-password security context.
    session_stub = Session(my_stub_config)
    # Use the create operation to create an authenticated session.
    session_id = session_stub.create()
    # Create a session ID security context.
    session_id_context = create_session_security_context(session_id)
    # Update the stub configuration with the session ID security context.
    my_stub_config.connector.set_security_context(session_id_context)
    return my_stub_config


def get_details(allnames, filename='serverlist.yaml'):
    """Get the details"""
    import sys
    from com.vmware.vcenter_client import VM
    from com.vmware.cis.tagging_client import TagAssociation
    from com.vmware.vapi import std_client
    vsphere_client = connect_vsphere()
    names_chunks = chunks(allnames, 100)
    results = []
    for names in names_chunks:
        names = set(names)
        vms = vsphere_client.vcenter.VM.list(VM.FilterSpec(names=names))
        sys.stdout.write('-')
        sys.stdout.flush()
        for vmserver in vms:
            sys.stdout.write('.')
            sys.stdout.flush()
            result = {}
            taglist = TagAssociation(connect_cis())
            taglist = taglist.list_attached_tags(
                std_client.DynamicID(type="VirtualMachine", id=vmserver.vm)
            )
            name = names.pop()
            result[name] = {}
            result[name] = taglist
            write_dict_to_file(result, filename)
            results.append(result)
    return results


def write_dict_to_file(mydict, filename):
    """Writes a dict to file"""
    import json
    myfile = open(filename, 'a')
    json.dump(mydict, myfile)
    myfile.write("\n")


def read_dicts_from_file(filename):
    """Reads a dict from file"""
    import yaml
    myfile = open(filename)
    results = []
    with myfile as infile:
        for line in infile:
            results.append(yaml.safe_load(line))
    return results


def get_unique_tags(results):
    """Get the tag details"""
    unique_tags = set()
    for server in results:
        for taglist in server:
            for tag in server[taglist]:
                unique_tags.add(tag)
    return unique_tags


def get_tag_details(unique_tags, connectcis=connect_cis()):
    """Get the details for each unique tag"""
    from com.vmware.cis.tagging_client import Tag, Category
    result = {}
    for tagid in unique_tags:
        result[tagid] = {}
        tagdetails = Tag(connectcis).get(tagid)
        catname = Category(connectcis).get(tagdetails.category_id).name
        result[tagid]['name'] = tagdetails.name
        result[tagid]['cat'] = catname
        # servertags += str(catname)+":"+str(tagdetails.name)+";"
    return result


def inject_tags_to_details(details, tagdetails):
    """Patch up the details with the full tag info"""
    result = {}
    for server in details:
        for taglist in server:
            result[taglist] = {}
            for tag in server[taglist]:
                result[taglist][tagdetails[tag]['cat']] = tagdetails[tag]['name']
    return result


def assemble_details(filename='serverlist.yaml'):
    """Grab the vm details from the file, get the tags, put them together"""
    details = read_dicts_from_file(filename)
    tagdetails = get_tag_details(get_unique_tags(details), connect_cis())
    return inject_tags_to_details(details, tagdetails)


def get_names(filename='servers.list'):
    """Get the list of server names"""
    with open(filename, 'r') as listfile:
        names = listfile.readlines()
    names = [x.strip() for x in names]
    return names


def main():
    """This is what I'm doing during dev"""
    # get_details(get_names('servers.list'), 'serverlist.yaml')
    # print assemble_details('serverlist.yaml')
    get_details(get_names('serverstmp.list'), 'serverlisttmp.yaml')
    print assemble_details('serverlisttmp.yaml')


if __name__ == "__main__":
    main()
