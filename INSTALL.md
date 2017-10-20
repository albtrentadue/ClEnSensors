# ClEnSensors
# Installation & Configuration Manual

This document describes the procedure to install and configure the Control Node software components and the Management Server software components which are used in the current state of development.

This manual includes description of installation of external components which are integrated into the ClEnSensor system. In this case, the manual will provide the necessary information to complete the installation without need to browse external documentation. However, for more detailed aspects of the external component, a link to the original component documentation will be provided.

# Control Node - Installation
This section describes the installation and configuration procedure of the **Control Node**.

The Control Code may be implemented using a processing unit (PC, embedded) capable to run a GNU/Linux version compliant with the specified SW requirements.

## HW Requirements
There are no specific HW requirements for the Control Node. However, the processing HW shall be capable to run smoothly a GNU/Linux kernel 3.19. The integration tests have been performed using an **eeePC** but even a Raspberry or other Linux embedded unit may be used. However it is **recommended** that, if the unit's main storage is implemented on a microSD memory, then the unit should be also equipped with an external HD for frequent data and file creation and modification. This because the microSD is not suitable for massive write/rewrite operation and excessive use as data storage may quickly lead to the memory module corruption.

## SW Requirements
### Operative system
The Control Node must have a GNU/Linux kernel 3 Operative System (OS). It is possible to use various different flavours of Linux, provided that they support the software components described in the following sections.

The current version of the Control Node SW has been integrated using **LinuxMint 17.3 "Rosa" - GNULinux kernel 3.19.0**.
Later versions of LinuxMint are expected to work as well.

### The SW owner OS user
It is recommended that the Control Node SW is not run as "root" user. A specific owner of the Control Node SW should be created in the OS. The system has been integrated with the installation directory owned by a user named "**clensensors**" but of course any name can be chosen. The documentation will assume in the following that the "clensensors" user has been created.

The SW owner can be created using the Linux command

```$ sudo useradd -s /bin/bash clensensors```

The "clensensors" user should be configured as a system administrator and must be enabled to use the serial communication.
Then it must belong to the following standard Linux user groups: adm, sudo, dialout, plugdev, netdev. To ensure the group belonging, the following command can be used:

```$ sudo usermod -G adm,sudo,dialout,plugdev,netdev clensensors```

After creation of the "clensensors" user, it is recommended to login to the Linux system using this user.

### Python support
The Control Node has been implemented in **Python 2.7**, therefore this version of Python must be available to the operative system.

The current version of Python can be verified by the command

```$ /usr/bin/python -V```

Python 3 is in general not supported. The Control Node has not been tested with Python 3 an therefore unknown problems may arise. 

**IMPORTANT**: if both versions 2.7 and 3 are installed in the Linux box, then the system must be configured to run Python 2.7 as default

Python native development libraries are needed to allow installation of the python libraries listed below. The **python-dev**  installable package is available as .deb package for LinuxMint. It can be installed using the standard package installation command apt-get:

```# sudo apt-get install python-dev```


#### Python Libraries
The following standard python library is required:
* **PySerial**

To test the availability of PySerial library, the following command must terminate with no error messages:

```$ python -c "import serial"```

If the library should be missing, it can be installed using the "pip" utility or by following the instructions in the PySerial library site https://pypi.python.org/pypi/pyserial/2.7

The following external python library is required:
* **Paho-1.3.x**

To test the availability of PySerial library, the following command must terminate with no error messages:

```$ python -c "import paho.mqtt.client as mqtt"```

If the library should be missing, it can be installed using the "pip" utility or by following the instructions in the Paho library site http://www.eclipse.org/paho


### RRD Tool
The Control Node uses the **RRDTool** round-robin database tool as local buffer storage system. RRDTool is an open source storage system suitable for the storage and analysis of numeric time series. RRDTool reference website is http://oss.oetiker.ch/rrdtool/

The RRDTool installable package is available as .deb package for LinuxMint. It can be installed using the standard package installation command apt-get:

```$ sudo apt-get install rrdtool```

RRDTool will require its python libraries to be installed as well to work with ClEnSensors

To test the availability of RRDTool Python library, the following command must terminate with no error messages:

```$ python -c "import rrdtool"```

If the library should be missing, it can be installed by means of the **python-rrdtool** package . The installable package is available as .deb package for LinuxMint. It can be installed using the standard package installation command apt-get:

```$ sudo apt-get install python-rrdtool```


The measures buffer storage physical location can be chosen within any directory for which the "clensensors" user has read/write permission. The default location is **/var/opt/clensensors**. Assuming the use of this location, it must be created in advance of the Control Node operation, using the commands:
```
$ sudo mkdir /var/opt/clensensors
$ sudo chown clensensors.clensensors /var/opt/clensensors
```

### MQTT Server Mosquitto
MQTT middleware needs a central MQTT Broker to dispatch messages. The MQTT Broker used in ClEnSensor is Mosquitto.

Mosquitto installable package is available as .deb package for LinuxMint. It can be installed using the standard package installation command apt-get:

```$ sudo apt-get install mosquitto```

The Mosquitto broker is installed as a Linux service. Its status can be verified as usual:

```$ sudo service mosquitto status```

Mosquitto configuration file is in /etc/mosquitto/mosquitto.conf

There are many configuration options available for the Mosquitto broker. The most relevant are settings related to SSL use to send encrypted messages. Please refer to Mosquitto documentation for more information on the website http://mosquitto.org

It is advisable to install also the mosquitto utilities to test and debug the messages exchanged by the modules. Such utilities are in the mosquitto-clients package:

```$ sudo apt-get install mosquitto-clients```
 
### Other useful SW components
Besides the necessary SW components, it is recommended to install on the Linux box the following utilities that may be needed to troubleshoot the system in case of problems.

#### ssh service
The Secure Shell service is useful to manage remotely the control node using a LAN connection. The **openssh-server**  installable package is available as .deb package for LinuxMint. It can be installed using the standard package installation command apt-get:

```# sudo apt-get install openssh-server```
 
#### The DiGi XCTU utility
The **XCTU** utility is the primary graphical interface provided by Digi to configure the **XBee** modules. It may be useful in order to verify of configure in the field a XBee module.
The XCTU installation binary file can be downloaded from the Digi website http://www.digi.com/
 
#### A Python IDE
Although the code has been tested before releasing it for use, further debugging activities may be need in case of troubleshooting. Therefore having a Python oriented IDE tool may turn to be useful.
Any IDE tool can be chosed at own preference. the **Idle** development tool has been used for the system integration:
 
```# sudo apt-get install idle``` 

## ClEnSensors Collector installation
The **ClEnSensors Collector** can be installed from the released package file named **ClEn_Collector-{version}.tgz**.
The package file is a tar compressed file including the pre-built software structure.

### Insatallation directory
The Collector can be installed inside any directory where the "clensensors" user has write and execution permission.
However, it may be desirable to install the software into commonly used locations in practice. This manual assumes that the installation directory will be created under the **/opt** directory, even though this is not a strict requirement.

**WARNING**: In case the software is replacing an existing version of the Collector, the installation package **will OVERWITE everything, including the configuration files!**. Since one doesn't generally want to lose the existing configuration, then it is mandatory to rename the existing installation directory before proceeding with the installation, like:

```# sudo mv clensensors clensensors_ORIG``` 

### Package installation
All the commands in this section shall be executed by the "clensensors" user, as it has been created with admin permissions in the OS.

To create the Collector installation structure, the released package file must be copied under **/opt**:

```$ sudo cp ClEn_Collector-<version>.tgz /opt```

Next, the file can be uncompressed

```
$ cd /opt
$ sudo tar xzf ClEn_Collector-{version}.tgz
```

Next, the directory permissions can be applied

```
$ sudo chown -R clensensors.clensensors ./clensensors
$ sudo chmod -R 755 ./clensensors
```

Next, specific permission may be set inside the installation directory

```
$ cd clensensors
$ chmod uga-x *.* LICENSE cfg/*.*
```

## ClEnSensors Collector configuration

*TBW*

# Management Software Installation

In the PoC2 version of ClEnSensors, the main software component in the Management Node is the **Dashboard**, and it is implemented by means od **EmonCMS**.

**EmonCMS** - https://emoncms.org/ - is an open source monitoring dashboard system and an integral part of the [OpenEnergyMonitor](https://openenergymonitor.org/emon/) open source project.

Within the ClEnSensors architecture the **Management Node** is logically separated from the **Control Node**. However it is possible to have both nodes installed on the same physical processing unit (card, PC, server...)-

The installation of the dashboard is indeed the installation of EmonCMS, then it is possible to follow the [documentation](https://github.com/emoncms/emoncms/blob/master/docs/LinuxInstall.md) available in the [EmonCMS project inside GitHub](https://github.com/emoncms/emoncms). However, the key steps are summrized in this manual, in case this documentation should be printed and thus not possible to browse the hyperlink to the project.

## SW Requirements

EmonCMS requires the following dependencies to be installed on the Linux OS of the Management Node:

`apache2, mysql-server, mysql-client, php, libapache2-mod-php, php-mysql, php-curl, php-pear, php-dev, php-mcrypt, php-json, git-core, redis-server, build-essential, ufw, ntp`.

**NOTE**: Emoncms website indicates 5.x as version to be uses. However newer versions of Ubuntu/Mint only support PHP-7 in relation to the `pear` package manager, therefore it is recommended to use the version 7.0 that is expected to work the same.

**NOTE**: at installation time, MySQL Server prompts for the 'root' superuser password. This password **must be kept at hand** for future uses.

The **dio**, **redis** and **swift mailer** php5 libraries are required. They can be installed by means of the pecl/pear utilities:

```
$ sudo pear channel-discover pear.swiftmailer.org 
$ sudo pecl install channel://pecl.php.net/dio-0.0.6 redis swift/swift

$ sudo sh -c 'echo "extension=dio.so" > /etc/php/7.0/apache2/conf.d/20-dio.ini' 
$ sudo sh -c 'echo "extension=dio.so" > /etc/php/7.0/cli/conf.d/20-dio.ini' 
$ sudo sh -c 'echo "extension=redis.so" > /etc/php/7.0/apache2/conf.d/20-redis.ini' 
$ sudo sh -c 'echo "extension=redis.so" > /etc/php/7.0/cli/conf.d/20-redis.ini'

$ sudo a2enmod rewrite
```

**NOTE**: Some linux versions may suffer from a bug that makes the "pecl install" fail during the installation phase of the libraries. In case the pecl command should fail, claiming a failed extraction of a compressed archive, you may want to download the uncompressed versions, by means of the **-Z option**:

```sudo pecl install -Z channel://pecl.php.net/dio-0.0.6 redis swift/swift```

### Apache2 web server configuration
There are few changes to apply to the Apache Web Server configuration: the **AllowOverride All** must be specified in the `<Directory /var/www/>` and `<Directory />`

At the end, the Apache web server needs to be restarted to include the recent changes.

```$ sudo service apache2 restart```

### Installing EmonCMS files
EmonCMS is a structure of php5 files that need to be installed inside the pages served by Apache.
The easiest way to install these files is to clone the git repository from within one of the directory served by the web server.
One (but not the only) choice is execute the git clone from the target directory, using these steps:
* Create the target directory "emoncms" under /var/www (the apache home direcrory):

```
$ cd /var/www
$ sudo mkdir emoncms
$ cd emoncms
$ sudo git clone -b stable https://github.com/emoncms/emoncms.git
```

* Since the EmonCMS PHP application has been installed outside the root directory of the Apache2 web server (/var/www/html) , a symbolic link must be created in the root directory pointing to the emoncms base dir:

```
$ cd /var/www/html
$ sudo ln -s ../emoncms
```

* Add on components must be installed inside the PHP structure

```
$ cd /var/www/emoncms/Modules

$ sudo git clone https://github.com/emoncms/dashboard.git
$ sudo git clone https://github.com/emoncms/app.git
```

* EmonCMS requires data repositories to be created in the filesystem:

```
sudo mkdir /var/lib/phpfiwa
sudo mkdir /var/lib/phpfina
sudo mkdir /var/lib/phptimeseries

sudo chown www-data.root /var/lib/phpfiwa
sudo chown www-data.root /var/lib/phpfina
sudo chown www-data.root /var/lib/phptimeseries
```

## Creating the database in MySQL

MySQL is used by EmonCMS as main data storage system. The installation procedure only requires to install the database area. The actual data objects are created automatically by the PHP code of EmonCMS.

Enter the MySQL engine as 'root' (requires the MySQL 'root' password):

```$ mysql -u root -p```

Then create database area and application user:

```
mysql> CREATE DATABASE emoncms;

mysql> CREATE USER 'emoncms'@'localhost' IDENTIFIED BY '<password>';
mysql> GRANT ALL ON emoncms.* TO 'emoncms'@'localhost';
mysql> flush privileges;

mysql> exit
```
**NOTE**: The emoncms user's password must be kept for the next step of the configuration and for future database maintenance operatios.

## Setting database settings in the PHP code

The file **"default.settings.php"** inside the **/var/www/emoncms** directory should be copied into a file named **"settings.php"**, then the copied file can be configured for the actual database settings:

```
$username = "emoncms";
$password = "<password>";
$server   = "localhost";
$database = "emoncms";
```

## Testing the configuration

At the end, browsing the initial page of EmonCMS should show the main login page:

http://localhost/emoncms/
