#! /bin/bash

cd
wget https://downloads.sourceforge.net/project/des/devel/2021-10-20/DESDevelLinux64SICStus.zip
unzip DESDevelLinux64SICStus.zip
rm DESDevelLinux64SICStus.zip
cd des
chmod u+x des des_start