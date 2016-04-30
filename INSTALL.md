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

### The SW owner OS user
It is recommended that the Control Node SW is not run as "root" user. A specific owner of the Control Node SW should be created in the OS. The system has been integrated with the installation directory owned by a user named "**clensensors**" but of course any name can be chosen. The documentation will assume in the following that the "clensensors" user has been created.

The SW owner can be created using the Linux command

```# sudo useradd -s /bin/bash clensensors```

The "clensensors" user should be configured as a system administrator and must be enabled to use the serial communication.
Then it must belong to the following standard Linux user groups: adm, sudo, dialout, plugdev, netdev. To ensure the group belonging, the following command can be used:

```# sudo usermod -G adm,sudo,dialout,plugdev,netdev clensensors```

After creation of the "clensensors" user, it is recommended to login to the Linux system using this user.

### Python support
The Control Node has been implemented in **Python 2.7**, therefore this version of Python must be available to the operative system.

The current version of Python can be verified by the command

```# /usr/bin/python -V```

Python 3 is in general not supported. The Control Node has not been tested with Python 3 an therefore unknown problems may arise. 

**IMPORTANT**: if both versions 2.7 and 3 are installed in the Linux box, then the system must be configured to run Python 2.7 as default

#### Python Libraries
The following standard python library is required:
* **PySerial**

To test the availability of PySerial library, the following command must terminate with no error messages:

```# python -c "import serial"```

If the library should be missing, it can be installed using the "pip" utility or by following the instructions in the PySerial library site https://pypi.python.org/pypi/pyserial/2.7

### RRD Tool
The Control Node uses the **RRDTool** round-robin database tool as local buffer storage system. RRDTool is an open source storage system suitable for the storage and analysis of numeric time series. RRDTool reference website is http://oss.oetiker.ch/rrdtool/

The RRDTool installable package is available as .deb package for LinuxMint. It can be installed using the standard package installation command apt-get:

 ```# sudo apt-get install rrdtool```


 
