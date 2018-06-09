"""
More VMWare play
"""


import configuration as conf

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


def connect_vsphere(hostname=conf.VM_HOSTNAME, debugoutput=False):
    """Connect to Vsphere"""
    import configuration as config
    import requests
    import urllib3
    import time
    from vmware.vapi.vsphere.client import create_vsphere_client
    connected = False
    while not connected:
        try:
            connected = True
            # Create a session object in the client.
            session = requests.Session()
            # We don't have valid certificates so...
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            session.verify = False
            vsphere_client = create_vsphere_client(
                server=hostname,
                username=config.VM_USERNAME,
                password=config.VM_PASSWORD,
                session=session
            )
        except:
            connected = False
            if debugoutput:
                print('\n' + hostname + ' won\'t talk to me :(\n')
            time.sleep(5)
    return vsphere_client


def connect_cis(vchostname, debugoutput=False):
    """Connect to CIS"""
    import configuration as config
    import requests
    import urllib3
    import time
    from com.vmware.cis_client import Session
    from vmware.vapi.security.user_password import create_user_password_security_context
    from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
    from vmware.vapi.lib.connect import get_requests_connector
    from vmware.vapi.security.session import create_session_security_context
    connected = False
    while not connected:
        try:
            connected = True
            # Create a session object in the client.
            session = requests.Session()
            # We don't have valid certificates so...
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            session.verify = False
            # Create a connection for the session.
            connector = get_requests_connector(
                session=session,
                url='https://' + vchostname + '/api'
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
        except:
            connected = False
            if debugoutput:
                print('\n' + vchostname + ' won\'t talk to me :(\n')
            time.sleep(5)
    return my_stub_config


def get_vms_in_vc(allnames, vchostname=conf.VM_HOSTNAME, debugoutput=False):
    """Get the VMs from allnames that are on vchostname"""
    import sys
    from com.vmware.vcenter_client import VM
    names_chunks = chunks(allnames, 50)
    if debugoutput:
        sys.stdout.write('Starting ' + vchostname + '\n')
        sys.stdout.flush()
    vmsfound = []
    vmcount = 0
    for names in names_chunks:
        names = set(names)
        if debugoutput == "Verbose" or debugoutput == "Insane":
            sys.stdout.write('Connecting...\n')
        vsphere_client = connect_vsphere(vchostname, debugoutput)
        if debugoutput == "Verbose" or debugoutput == "Insane":
            sys.stdout.write('Connected.\n')
        if debugoutput == "Insane":
            sys.stdout.write('The names we are looking for are:\n')
            sys.stdout.write(str(names))
            sys.stdout.flush()
        vms = vsphere_client.vcenter.VM.list(VM.FilterSpec(names=names))
        if debugoutput == "Verbose" or debugoutput == "Insane":
            sys.stdout.write('\nQueried.\n')
            sys.stdout.flush()
        vmsfound.append(vms)
        sys.stdout.flush()
        vmcount += len(vms)
        if debugoutput == "Verbose" or debugoutput == "Insane":
            sys.stdout.write('In this chunk, we found ' + str(len(vms)) + ' systems on ' + vchostname + '\n')
            sys.stdout.flush()
    if debugoutput:
        sys.stdout.write(vchostname + ' has ' + str(vmcount) + ' of the systems we seek\n')
        sys.stdout.flush()
    return vmsfound


def get_details(allnames, vchostname=conf.VM_HOSTNAME, debugoutput=False):
    """Get the details"""
    import sys
    from com.vmware.cis.tagging_client import TagAssociation
    from com.vmware.vapi import std_client
    results = []
    vmcount = 0
    vmchunks = get_vms_in_vc(allnames, vchostname, debugoutput)
    for vms in vmchunks:
        vmChunkProgress = 0
        for vmserver in vms:
            vmChunkProgress += 1
            vmcount += 1
            result = {}
            taglist = TagAssociation(connect_cis(vchostname, debugoutput))
            taglist = taglist.list_attached_tags(
                std_client.DynamicID(type="VirtualMachine", id=vmserver.vm)
            )
            result[vmserver.name] = {}
            result[vmserver.name] = taglist
            results.append(result)
            if debugoutput:
                if vmcount == 1:
                    sys.stdout.write('\rThis chunk has processed ' + str(vmChunkProgress) + 'VM')
                else:
                    sys.stdout.write('\rThis chunk has processed ' + str(vmChunkProgress) + 'VMs')
                sys.stdout.flush()
    if debugoutput:
        sys.stdout.write('\nDone looking up VMs on this VC')
        sys.stdout.flush()
    return results


def get_unique_tags(results):
    """Get the tag details"""
    unique_tags = set()
    for server in results:
        for taglist in server:
            for tag in server[taglist]:
                unique_tags.add(tag)
    return unique_tags


def get_tag_details(unique_tags, vchostname, debugoutput = False):
    """Get the details for each unique tag"""
    import sys
    from com.vmware.cis.tagging_client import Tag, Category
    result = {}
    if debugoutput:
        sys.stdout.write('\nLooking up tags on ' + vchostname + ' now\r')
        sys.stdout.flush()
    tagcount = 0
    for tagid in unique_tags:
        connectcis = connect_cis(vchostname, debugoutput)
        tagcount += 1
        result[tagid] = {}
        tagdetails = Tag(connectcis).get(tagid)
        catname = Category(connectcis).get(tagdetails.category_id).name
        result[tagid]['name'] = tagdetails.name
        result[tagid]['cat'] = catname
        # servertags += str(catname)+":"+str(tagdetails.name)+";"
        if debugoutput:
            sys.stdout.write('\rLooking up tags on ' + vchostname + ' now - found ' + str(tagcount) + '')
            sys.stdout.flush()
    if debugoutput:
        sys.stdout.write('\rWe found ' + str(tagcount) + ' tags on ' + vchostname + '\n\n')
        sys.stdout.flush()
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


def assemble_details(vchostname, details, debugoutput=False):
    """Grab the vm details from the file, get the tags, put them together"""
    tagdetails = get_tag_details(get_unique_tags(details), vchostname, debugoutput)
    return inject_tags_to_details(details, tagdetails)


def get_names(filename=conf.VMLISTFILE):
    """Get the list of server names"""
    with open(filename, 'r') as listfile:
        names = listfile.readlines()
    names = [x.strip() for x in names]
    return names


def get_vmtag_data(debugoutput=False, nameslist=get_names(conf.VMLISTFILE)):
    """Get all the data and put it together"""
    import pickle
    details = []
    if isinstance(conf.VM_HOSTNAME, list):
        for vchostname in conf.VM_HOSTNAME:
            details += get_details(nameslist, vchostname, debugoutput)
            returnvalue = assemble_details(vchostname, details, debugoutput)
    else:
        details += get_details(nameslist, conf.VM_HOSTNAME, debugoutput)
        returnvalue = assemble_details(conf.VM_HOSTNAME, details, debugoutput)
    with open(conf.VMTAGDETAILSFILE, 'wb') as datafile:
        pickle.dump(returnvalue, datafile)
    return returnvalue


if __name__ == "__main__":
    print get_vmtag_data(True)
