#! /bin/bash

cd
echo $PWD
rm -rf ./des/
rm DESDevelLinux64SICStus.zip
wget -nv https://downloads.sourceforge.net/project/des/devel/2021-12-12/DESDevelLinux64SICStus.zip
unzip DESDevelLinux64SICStus.zip
rm DESDevelLinux64SICStus.zip
cd des
echo $PWD
chmod u+x des des_start
