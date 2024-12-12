#! /bin/bash

cd $GITHUB_WORKSPACE
rm -rf ./des/
rm DESDevelLinux64SICStus.zip
wget -nv https://downloads.sourceforge.net/project/des/devel/2021-12-12/DESDevelLinux64SICStus.zip
unzip DESDevelLinux64SICStus.zip
rm DESDevelLinux64SICStus.zip
cd des
chmod u+x des des_start

DES_PATH=`readlink -f des_start`
echo "Instalado DES en ${DES_PATH}"
