# Compile All The Things

This is my attempt to put a bunch of data in one place.

### The first step on the path to insanity (How to make the landscape api work on RHEL):

  - On an Ubuntu System:
    - apt-get download landscape-api
    - mkdir ~/tmp
    - dpkg-deb -R landscape-api_17.03.2-0ubuntu0.16.04.1_all.deb tmp/
  - On the RHEL system:
    - `rsync -av <UbuntuServer>:<Path>/tmp .`
    - chown -R root tmp
    - rsync -av tmp/usr/* /usr/
    - pushd /usr/lib/python2.7/site-packages/
    - ln -s ../dist-packages/landscape_api .
    - popd

### Installing the google api client
easy_install --upgrade google-api-python-client

### VM Tags
Originally this just found the tag categoy, tag name, and ID for each VM and output them to a file.  This was really really slow and often died half way through.

Since the python script is orders of magnitude faster than the VMWare API, I do this differently now.

First the script grabs the ID of VMs from the vcenter along with the tags it has associated with the vm.  This is put in a file.  

The file is then loaded back and a set of unique tags is created.  We then lookup each tag - finding it's related category and it's name.  We create an array of these with the tag id as the key.  Since there is a lot of tag re-use, this is much faster than looking up each tag for each VM.

We then iterate through the VM list from step one, adding in the tag details based on the tag id in both data sets matching.

I have considered simplifying further by using a similar process to simplify tag categories, but I don't think this is needed.

Also of note, some of the API can't handle more than 128 VMs, so they are broken into sets of up to 100 for processing.

