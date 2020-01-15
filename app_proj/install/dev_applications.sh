#!/bin/sh
# INSTALL DEV APPLICATIONS

sudo apt-get update        						

sudo apt-get install lubuntu-desktop -y			

sudo apt-get install pgadmin3

sudo apt-get install libreoffice -y				
sudo apt-get remove abiword gnumeric

sudo apt-get install pinta -y

sudo apt-get install gnome-search-tool -y

sudo add-apt-repository ppa:notepadqq-team/notepadqq
sudo apt-get update        						
sudo apt-get install notepadqq -y

sudo add-apt-repository "deb http://archive.canonical.com/ $(lsb_release -sc) partner"
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install skype


