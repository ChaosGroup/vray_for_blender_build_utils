## General

This document covers the usage of the automated build system. It could be used to build offical Blender and Blender with V-Ray additions. Script will download and update Blender source code, dependencies, install exporter add-on, generate installer, etc.


## Prerequirements


### Git
* **Windows**: [msysgit](http://code.google.com/p/msysgit/downloads/list)
* **Linux** (Ubuntu): `sudo apt-get install git`
* **OS X**: Could already present in the system. Use any preffered way to install git.


### Subversion
* Used on **OS X** and **Windows** only to download dependent librarires
* **Windows**: [http://www.sliksvn.com/en/download SlikSVN]
* **OS X**: Could already present in the system. Use any preffered way to install git.


### CMake

* http://www.cmake.org/
* Make sure _cmake_ executable is added to **PATH** environment variable and is available from command line.


### Ninja

* **Windows**: Embedded in vb25-patch
* **Linux**: Use package manager or compile from source (http://martine.github.io/ninja/)
* **OS X**: Use some package manager or compile from source (http://martine.github.io/ninja/)
  * Make sure _ninja_ executable is added to **PATH** environment variable and is available from command line.


### Python 3

* **Windows**: [Python 3.4.2 x64](https://www.python.org/ftp/python/3.4.2/python-3.4.2.amd64.msi) or later
  * Make sure _python_ executable is added to **PATH** environment variable and is available from command line.
* **Linux**: Use package manager to install Python 3.
* **OS X**: Use any preffered way to install Python 3.


### Optional

* **Windows** only: Install [NSIS](http://nsis.sourceforge.net/Download), if you want to generate an installer.


## Getting the script

Create some directory for building, start terminal application and navigate to it.
Examples:

* **Linux** / **OS X**:
```
mkdir ~/build/vb30
cd ~/build/vb30
```

* **Windows**:
```
mkdir C:\build
cd C:\build
```

Now clone **vb25-patch** repo:
```
git clone git://github.com/bdancer/vb25-patch.git
```

### Dependencies (Linux only)

This is needed only once before the very first compilation:
```
python vb25-patch/build.py --install_deps
```

Depenging on a Linux distribution it will install appropriate packages or build dependencies from source.

This step is tested mostly on Ubuntu LTS. Please, contact me if you're expriencing any issues here.

### Compilation

In the most simple case you'll have to type smth like this:

* **Windows**: `python vb25-patch/build.py --vc2013`
* **Linux** / **OS X**: `python vb25-patch/build.py`

You could also create a script wrapper to automate things even more and not to type command line options all the time.

* **Windows**:

```
@echo off

cd vb25-patch
git pull --rebase
cd ..

python vb25-patch/build.py ^
--uppatch=off       ^ :: Already updated
--with_game         ^ :: Build Game Engine support
--with_player       ^ :: Build Blender Player
--with_collada      ^ :: OpenCollada support
--with_cycles       ^ :: Enable Cycles
--vc2013            ^ :: Use this flag if you've installed Visual Studio 2013 (which is preffered)
--release --package ^ :: This will generate NSIS archive (if NSIS is installed)
%*
```

* **Linux** / **OS X**:

```
# Update vb25-patch before building:
cd vb25-patch
git pull
cd ..

python vb25-patch/build.py \
--uppatch=off        \
--release --package  \
--with_game          \
--with_player        \
--with_cycles        \
--builddir=/tmp/vb30 \
$*
```

Running this script will clone (or update if already cloned) Blender sources, library dependencies (Windows / OS X), etc and compile a fresh Blender build.

### Paths

By default you'll find build installation under:
```
BUILD_DIRECTORY/install/
```
and installer / archive under:
```
BUILD_DIRECTORY/release/
```


### Naming

```
vrayblender3-2.73-58783-67fcf52-6f8d89a-x86_64-windows.exe
             ^^^^ ^^^^^ ^^^^^^^ ^^^^^^^ ^^^^^^ ^^^^^^^
             |    |     |       |       |      `-  Operating system
             |    |     |       |       `- Architecture
             |    |     |       `- V-Ray patches revision
             |    |     `- Blender master revision
             |    `- Commint count
             `--- Blender version
```


### Contacts

* Issues tracker: https://github.com/bdancer/vb25-patch/issues
* Email: Andrei Izrantcev andrei.izrantcev@chaosgroup.com
