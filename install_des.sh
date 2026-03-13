#! /bin/bash

cd $GITHUB_WORKSPACE
rm -rf ./des/
rm DES6.8Linux64SICStus.zip
wget -nv https://sourceforge.net/projects/des/files/devel/2026-03-10/DESDevelLinux64SICStus.zip/download -O DESLinux64SICStus.zip
unzip DESLinux64SICStus.zip
rm DESLinux64SICStus.zip
cd des
chmod u+x des des_start

DES_PATH=`readlink -f des_start`
echo "Instalado DES en ${DES_PATH}"
