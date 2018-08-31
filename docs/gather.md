# Gather environment details

[<- Back to the overview](../README.md)

You can use the following action variable to gather environment details from your environment.

```yml
gather: True
```

If not specified (or specified as `False`), no environment details will be gathered.

Otherwise, the following details will be gathered:

- The hostname of each server operating as part of the environment
- `Version.xml` file from each host in the environment (except the UG tier in v11.7)
- Information Server version number
- JDK version and patch level for each component (Information Server, WebSphere Application Server)
- Database type of the installation
- Operating System version
- Kernel version
- Compiler version (engine tier)
- WebSphere Application Server version (domain tier)

These details will be consolidated into the file `envdetails.txt` in the location defined by the `ibm_infosvr_impexp_fetch_location` variable (see `defaults/main.yml`), with each Version.xml placed in the same location and pre-pended with the hostname from which it was retrieved.

[<- Back to the overview](../README.md)
