#! /bin/bash

cd /tmp
# wget https://download.oracle.com/otn_software/linux/instantclient/19800/instantclient-basic-linux.x64-19.8.0.0.0dbru.zip
wget https://download.oracle.com/otn_software/linux/instantclient/217000/instantclient-basic-linux.x64-21.7.0.0.0dbru.zip
unzip instantclient-basic-linux.x64-21.7.0.0.0dbru.zip
ln -s /tmp/instantclient_21_7 /tmp/instantclient
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/tmp/instantclient
