# ClEnSensors
# Installation & Configuration Manual

This document describes the procedure to install and configure the Control Node software components and the Management Server software components which are used in the current state of development.

This manual includes description of installation of external components which are integrated into the ClEnSensor system. In this case, the manual will provide the necessary information to complete the installation without need to browse external documentation. However, for more detailed aspects of the external component, a link to the original component documentation will be provided.

# Control Node - Installation
This section describes the installation and configuration procedure of the **Control Node**.

The Control Code may be implemented using a processing unit (PC, embedded) capable to run a GNU/Linux version compliant with the specified SW requirements.

## HW Requirements
There are no specific HW requirements for the Control Node. However, the processing HW shall be capable to run smoothly a GNU/Linux kernel 3.19. The integration tests have been performed using an **eeePC** but even a Raspberry or other Linux embedded unit may be used. However it is **recommended** that, if the unit's main storage is implemented on a microSD memory, then the unit should be also equipped with an external HD for ferquent data and file creation and modification. This because the microSD is not suitable for massive write/rewrite operation and excessive use as data storage may quickly lead to the memory module corruption.

## SW Requirements
### Operative system
The Control Node must have a GNU/Linux kernel 3.19 operative system. It is possible to use various differen variant of Linux, provided that they support the software components described in the following sections
