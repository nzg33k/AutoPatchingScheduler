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
