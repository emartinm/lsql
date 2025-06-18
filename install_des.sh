#! /bin/bash

cd $GITHUB_WORKSPACE
rm -rf ./des/
rm DES6.8Linux64SICStus.zip
wget -nv https://sourceforge.net/projects/des/files/des/des6.8/DES6.8Linux64SICStus.zip/download -O DES6.8Linux64SICStus.zip
unzip DES6.8Linux64SICStus.zip
rm DES6.8Linux64SICStus.zip
cd des
chmod u+x des des_start

DES_PATH=`readlink -f des_start`
echo "Instalado DES en ${DES_PATH}"
