import os
import sys
import subprocess
import stat
import re


WIN = "windows"
LNX = "linux"
MAC = "macos"


def getHostOs():
	if sys.platform == "win32":
		return WIN
	elif sys.platform.find("linux") != -1:
		return LNX
	elif sys.platform == "darwin":
		return MAC

def consolePrint(arg):
	if getHostOs() == MAC:
		sys.stderr.write(arg)
		sys.stderr.flush()
	else:
		sys.stdout.write(arg)
		sys.stdout.flush()

def writeShortcut(path):
	ofile = open("/usr/share/applications/vrayblender.desktop", 'w')
	ofile.write("[Desktop Entry]\n")
	ofile.write("Name=V-Ray/Blender\n")
	ofile.write("Exec=sh \"%s/blender\"\n" % path)
	ofile.write("Icon=%s/blender.svg\n" % path)
	ofile.write("Terminal=true\n")
	ofile.write("Type=Application\n")
	ofile.write("Categories=Graphics;3DGraphics;\n")
	ofile.write("StartupNotify=false\n")
	ofile.write("MimeType=application/x-blender;\n")
	ofile.close()


def writeWrapper(installPath, appsdkPath):
	wrapperString = """#/bin/bash
export LD_LIBRARY_PATH="%s":"%s":$LD_LIBRARY_PATH
%s
"%s/blender.bin"
"""
	blenderPath = os.path.join(installPath, 'blender')
	blenderPathBin = os.path.join(installPath, 'blender.bin')

	if os.path.isfile(blenderPathBin):
		backUp = blenderPathBin + '.bk'
		if os.path.exists(backUp):
			os.path.remove(backUp)
		print('Removing old "%s"' % blenderPathBin)
		os.rename(blenderPathBin, backUp)

	print('Moving "%s" to "%s"' % (blenderPath, blenderPathBin))
	os.rename(blenderPath, blenderPathBin)
	print('Writing blender launcher')
	qtPluginPath = ''
	if getHostOs() == LNX:
		qtPluginPath = 'export QT_PLUGIN_PATH="%s"' % os.path.join(installPath, '..', 'V-Ray', 'VRayZmqServer', 'appsdk')
	with open(blenderPath, 'w+') as f:
		f.write(wrapperString % (installPath, appsdkPath, qtPluginPath, installPath.rstrip('/')))


def setExecBits(installPath):
	flags = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
	st = os.stat(os.path.join(installPath, 'blender'))
	os.chmod(os.path.join(installPath, 'blender'), st.st_mode | flags)

	st = os.stat(os.path.join(installPath, 'blender.bin'))
	os.chmod(os.path.join(installPath, 'blender.bin'), st.st_mode | flags)

	st = os.stat(os.path.join(installPath, 'blenderplayer'))
	os.chmod(os.path.join(installPath, 'blenderplayer'), st.st_mode | flags)


def parseLdconfig():
	output, err = subprocess.Popen(["ldconfig", "-p", "-v"], stdout=subprocess.PIPE).communicate()
	if err is not None:
		sys.exit(-1)
	libsList = []
	for line in [ll.strip() for ll in str(output).split('\n')][1:]:
		match = re.match(r'^([^\s]*?)\s.*?=>\s(.*?)$', line, re.I | re.S)
		if match:
			libsList.append(match.groups())
	return libsList


def symlinkLib(installPath, missingLib, sysLibs):
	# find suitable lib version to link

	def parseLibName(fullName):
		return '.so.'.join(fullName.split('.so.')[0:-1]), fullName.split('.so.')[-1]

	missingLibName = parseLibName(missingLib)[0]
	candidates = []
	for lib in sysLibs:
		if missingLibName == parseLibName(lib[0])[0]:
			candidates.append(lib)

	#find the lowest version that is higher or equal than needed
	candidates.sort(key=lambda pair: pair[0])
	missingVer = parseLibName(missingLib)[1]
	for candidate in candidates:
		if parseLibName(candidate[0])[1] >= missingVer:
			if subprocess.call('ln -s %s %s' % (candidate[1], os.path.join(installPath, missingLib))) != 0:
				sys.exit(-1)


def writeSoSymlinks(installPath):
	sysLibs = parseLdconfig()
	output, err = subprocess.Popen(["sudo", "ldd", os.path.join(installPath, 'blender.bin')], stdout=subprocess.PIPE).communicate()
	if err is not None:
		sys.exit(-1)
	for libLine in [ll.strip() for ll in str(output).split('\n')]:
		if libLine.find('not found') != -1:
			symlinkLib(installPath, libLine.split('=>')[0].strip(), sysLibs)


def fixPermitions(installPath):
	sudo = 'sudo' if getHostOs() == LNX else ''
	if 'CHAOS_INSTALL_ORIGINAL_USER_NAME' not in os.environ or\
		os.environ['CHAOS_INSTALL_ORIGINAL_USER_NAME'] == '' or\
		os.environ['CHAOS_INSTALL_ORIGINAL_USER_NAME'] == 'root':

		# make all files writable by all
		consolePrint('Changing permitions for %s files to a+rw\n' % installPath)
		os.system('%s chmod -R a+rw "%s"' % (sudo, installPath))
	else:
		# make the original installer the owner
		owner = os.environ['CHAOS_INSTALL_ORIGINAL_USER_NAME']
		consolePrint('Changing owner for %s files to %s\n' % (installPath, owner))
		os.system('%s chown -R %s "%s"' % (sudo, owner, installPath))


if __name__ == '__main__':
	installPath = os.path.dirname(os.path.realpath(sys.argv[0]))
	appsdkPath = ''
	if len(sys.argv) == 2:
		appsdkPath = os.path.dirname(sys.argv[1])
	consolePrint('Running postinstall.py for installPath="%s"\n' % installPath)

	current_os = getHostOs()
	if current_os != WIN:
		if current_os == LNX:
			writeShortcut(installPath)
			writeWrapper(installPath, appsdkPath)
			setExecBits(installPath)
			writeSoSymlinks(installPath)

		fixPermitions(installPath)
		if appsdkPath != '':
			zmq_path = os.path.normpath(os.path.join(appsdkPath, '..', '..'))
			fixPermitions(zmq_path)
