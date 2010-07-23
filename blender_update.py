__author__ = "Andrey M. Izrantsev http://cgdo.ru"
__version__ = "1.0"

import sys
import os
import shutil
import socket
import platform
import getpass
import re

from optparse import OptionParser

USER= getpass.getuser()
PLATFORM= sys.platform
HOSTNAME= socket.gethostname()
ARCH= platform.architecture()[0]
REV= 'current'

'''
  COMMAND LINE OPTIONS
'''
parser= OptionParser(usage="%prog [options]", version="blender_update %s by %s" % (__version__, __author__))

parser.add_option(
	'-b',
	'--blender',
	action= 'store_true',
	dest= 'pure_blender',
	default= False,
	help= 'Build Blender 2.5 SVN (don\'t apply V-Ray/Blender patches).'
)

parser.add_option(
	'-a',
	'--archive',
	action= 'store_true',
	dest= 'archive',
	default= False,
	help= 'Create archive (Linux) or installer (Windows, NSIS required).'
)

parser.add_option(
	'-r',
	'--rebuild',
	action= 'store_true',
	dest= 'rebuild',
	default= False,
	help= 'Full rebuild.'
)

parser.add_option(
	'-d',
	'--docs',
	action= 'store_true',
	dest= 'docs',
	default= False,
	help= 'Build Python API documentation (python-sphinx required).'
)

parser.add_option(
	'-c',
	'--collada',
	action= 'store_true',
	dest= 'with_collada',
	default= False,
	help= 'Add Collada support.'
)

parser.add_option(
	'-g',
	'--debug',
	action= 'store_true',
	dest= 'debug',
	default= False,
	help= 'Debug build.'
)

parser.add_option(
	'-j',
	'--jobs',
	action= 'store_true',
	dest= 'jobs',
	default= 4,
	help= 'Number of build jobs.'
)

parser.add_option(
	'-o',
	'--optimize',
	action= 'store_true',
	dest= 'optimize',
	default= False,
	help= 'Use compiler optimizations.'
)

parser.add_option(
	'-u',
	'--update',
	action= 'store_true',
	dest= 'update',
	default= False,
	help= 'Update sources.'
)

parser.add_option(
	'-p',
	'--update_patch',
	action= 'store_true',
	dest= 'update_patch',
	default= False,
	help= 'Update patch sources.'
)

parser.add_option(
	'-t',
	'--test',
	action= 'store_true',
	dest= 'test',
	default= False,
	help= 'Test mode.'
)

if PLATFORM == "win32":
	parser.add_option(
		'-i',
		'--installdir',
		action= 'store_true',
		dest= 'installdir',
		default= "C:\\\\release\\\\",
		help= 'Installation directory.'
	)
else:
	parser.add_option(
		'-i',
		'--installdir',
		action= 'store_true',
		dest= 'installdir',
		default= "/opt/",
		help= 'Installation directory.'
	)

(options, args) = parser.parse_args()

if(len(sys.argv) == 1):
	parser.print_version()
	parser.print_help()
	sys.exit()

'''
  MAIN SECTION
'''
project= 'vb25'
if options.pure_blender:
	project= 'blender-2.5'

install_dir= os.path.join(options.installdir,project)

release_dir= "/home/bdancer/devel/vrayblender/release"

BF_NUMJOBS= options.jobs
if not HOSTNAME.find('vbox') == -1:
	BF_NUMJOBS= 1

BF_PYTHON_VERSION= '3.1'

def notify(title, message):
	if not PLATFORM == "win32":
		os.system("notify-send \"%s\" \"%s\"" % (title, message))

def generate_installer(patch_dir, BF_INSTALLDIR, INSTALLER_NAME):
	SKIP_DIRS= ('plugins')

	#
	# NSIS installer sciprt template;
	# based on official script by jesterKing
	#
	ns = open(os.path.join(patch_dir,'installer','template.nsi'),"r")
	ns_cnt = str(ns.read())
	ns.close()
	
	ns_cnt = string.replace(ns_cnt, "[PYTHON_VERSION]", BF_PYTHON_VERSION)

	# do root
	rootlist = []
	rootdir = os.listdir(BF_INSTALLDIR+"\\")
	for rootitem in rootdir:
		if os.path.isdir(BF_INSTALLDIR+"\\"+ rootitem) == 0:
			rootlist.append("File \"" + os.path.normpath(BF_INSTALLDIR) + "\\" + rootitem+"\"")
	rootstring = string.join(rootlist, "\n  ")
	rootstring += "\n\n"
	ns_cnt = string.replace(ns_cnt, "[ROOTDIRCONTS]", rootstring)

	dot_blender_str= ""
	dot_blender_del= ""
	scripts_dirs= []
	for root, dirs, files in os.walk(os.path.join(BF_INSTALLDIR, ".blender")):
		root_path= string.replace(root, BF_INSTALLDIR, "")
		dot_blender_str+= '\n  SetOutPath \"$BLENDERHOME%s\"\n'%(root_path)
		scripts_dirs.append(root_path)
		for f in os.listdir(root):
			f_path= os.path.join(root,f)
			if os.path.isdir(f_path) == 0:
				dot_blender_del+= '  Delete \"$INSTDIR%s%s\"\n'%(root_path,f)
				dot_blender_str+= '  File \"%s\"\n'%(f_path)
	ns_cnt = string.replace(ns_cnt, "[DOTBLENDER]", dot_blender_str)

	scripts_dirs.reverse()
	for sdir in scripts_dirs:
		dot_blender_del+= '  RMDir /r \"$INSTDIR%s\"\n'%(sdir)

	# do delete items
	delrootlist = []
	for rootitem in rootdir:
		if os.path.isdir(BF_INSTALLDIR + rootitem) == 0:
			delrootlist.append("Delete $INSTDIR\\" + rootitem)
	delrootstring = string.join(delrootlist, "\n  ")
	delrootstring+= "\n\n"

	ns_cnt = string.replace(ns_cnt, "[DELROOTDIRCONTS]", delrootstring)
	ns_cnt = string.replace(ns_cnt, "[DOTBLENDER_DELETE]", dot_blender_del)

	plugincludelist = []
	plugincludepath = "%s%s" % (BF_INSTALLDIR, "\\plugins\\include")
	plugincludedir = os.listdir(plugincludepath)
	for plugincludeitem in plugincludedir:
		plugincludefile = "%s\\%s" % (plugincludepath, plugincludeitem)
		if os.path.isdir(plugincludefile) == 0:
			if plugincludefile.find('.h') or plugincludefile.find('.DEF'):
				plugincludefile = os.path.normpath(plugincludefile)
				plugincludelist.append("File \"%s\"" % plugincludefile)
	plugincludestring = string.join(plugincludelist, "\n  ")
	plugincludestring += "\n\n"
	ns_cnt = string.replace(ns_cnt, "[PLUGINCONTS]", plugincludestring)

	ns_cnt = string.replace(ns_cnt, "DISTDIR",  BF_INSTALLDIR)
	ns_cnt = string.replace(ns_cnt, "SHORTVER", VERSION)
	ns_cnt = string.replace(ns_cnt, "VERSION",  VERSION)
	ns_cnt = string.replace(ns_cnt, "RELDIR",   DIR)
	ns_cnt = string.replace(ns_cnt, "[INSTALLER_DIR]", INSTALLER_DIR)
	ns_cnt = string.replace(ns_cnt, "[INSTALLER_NAME]", INSTALLER_NAME)

	inst_nsis= os.path.join(DIR,"installer.nsi")
	new_nsis = open(inst_nsis, 'w')
	new_nsis.write(ns_cnt)
	new_nsis.close()

	if not options.test:
		os.system("makensis \"%s\""%(inst_nsis))


def generate_user_config(filename):
	ofile= open(filename, 'w')
	ofile.write("# This file is automatically generated: DON\'T EDIT!\n")

	build_options= {
		'True': [
			'WITH_BF_INTERNATIONAL',
			'WITH_BF_JPEG',
			'WITH_BF_PNG',
			'WITH_BF_FFMPEG',
			'WITH_BF_OPENAL',
			'WITH_BF_SDL',
			'WITH_BF_BULLET',
			'WITH_BF_ZLIB',
			'WITH_BF_FTGL',
			'WITH_BF_RAYOPTIMIZATION',
			'WITH_BUILDINFO',
			'WITH_BF_OPENEXR'
		],
		'False': [
			'WITH_BF_QUICKTIME',
			'WITH_BF_FMOD',
			'WITH_BF_ICONV',
			'WITH_BF_STATICOPENGL',
			'WITH_BF_VERSE',
			'WITH_BF_GAMEENGINE',
			'WITH_BF_PLAYER',
		]
	}
	# Check this option:
	#  'WITH_BF_FHS' (Use the Unix "Filesystem Hierarchy Standard" rather then a redistributable directory layout)

	# if PLATFORM == "win32" and ARCH == '64bit':
	# 	build_options['False'].append('WITH_BF_JACK')
	# 	build_options['False'].append('WITH_BF_SNDFILE')
	# 	build_options['False'].append('WITH_BF_FFMPEG')
	# 	build_options['False'].append('WITH_BF_OPENAL')

	# if PLATFORM == "win32":
	# 	build_options['False'].append('WITH_BF_OPENEXR')
	# else:
	# 	build_options['True'].append('WITH_BF_OPENEXR')

	if options.with_collada:
		build_options['True'].append('WITH_BF_COLLADA')
	else:
		build_options['False'].append('WITH_BF_COLLADA')

	if options.debug:
		build_options['True'].append('BF_DEBUG')

	for key in build_options:
		for opt in build_options[key]:
			ofile.write("%s = '%s'\n"%(opt,key))

	# ofile.write("BF_OPENEXR_LIBPATH = \"#../lib/windows/openexr/lib_vs2010\"\n")
	# ofile.write("BF_OPENEXR_INC= \"#../lib/windows/openexr/include_vs2010 #../lib/windows/openexr/include_vs2010/IlmImf #../lib/windows/openexr/include_vs2010/Iex #../lib/windows/openexr/include_vs2010/Imath\"\n")

	ofile.write("BF_OPENAL_LIB = \'openal alut\'\n")
	ofile.write("BF_TWEAK_MODE = \'false\'\n")
	ofile.write("BF_PYTHON_VERSION = \'%s\'\n" % BF_PYTHON_VERSION)
	ofile.write("BF_NUMJOBS = %i\n" % BF_NUMJOBS)

	ofile.write("BF_INSTALLDIR = \"%s\"\n" % os.path.join(options.installdir,project))
	if PLATFORM == "win32" :
		ofile.write("BF_SPLIT_SRC = \'true\'\n")
		# Optimal build path to avoid bugs when using scons
		ofile.write("BF_BUILDDIR = \"C:\\\\b\"\n")
	else:
		ofile.write("BF_BUILDDIR = \"/tmp/build-%s\"\n" % project)
		if options.optimize: # Optimize for Intel Core
			ofile.write("CCFLAGS = [\'-pipe\',\'-fPIC\',\'-march=nocona\',\'-msse3\',\'-mmmx\',\'-mfpmath=sse\',\'-funsigned-char\',\'-fno-strict-aliasing\',\'-ftracer\',\'-fomit-frame-pointer\',\'-finline-functions\',\'-ffast-math\']\n")
			ofile.write("CXXFLAGS = CCFLAGS\n")
			ofile.write("REL_CFLAGS = [\'-O3\',\'-fomit-frame-pointer\',\'-funroll-loops\']\n")
			ofile.write("REL_CCFLAGS = REL_CFLAGS\n")
		else:
			ofile.write("CCFLAGS = [\'-pipe\',\'-fPIC\',\'-funsigned-char\',\'-fno-strict-aliasing\']\n")
			ofile.write("CPPFLAGS = [\'-DXP_UNIX\']\n")
			ofile.write("CXXFLAGS = [\'-pipe\',\'-fPIC\',\'-funsigned-char\',\'-fno-strict-aliasing\']\n")
			ofile.write("REL_CFLAGS = [\'-O2\']\n")
			ofile.write("REL_CCFLAGS = [\'-O2\']\n")

		ofile.write("C_WARN = [\'-Wno-char-subscripts\', \'-Wdeclaration-after-statement\']\n")
		ofile.write("CC_WARN = [\'-Wall\']\n")

	ofile.close()

notify("%s SVN update" % project, "Started...")

working_directory= os.getcwd()

# Update||obtain Blender SVN
blender_dir= os.path.join(working_directory,'blender')
if os.path.exists(blender_dir):
	os.chdir(blender_dir)
	if options.update:
		sys.stdout.write("Updating Blender sources\n")
		if not options.test:
			os.system("svn update")

	try:
		entries= open(os.path.join(blender_dir,'.svn','entries'), 'r').read()
	except IOError:
		pass
	else:
		if re.match('(\d+)', entries):
			rev_match= re.search('\d+\s+dir\s+(\d+)', entries)
			if rev_match:
				REV= rev_match.groups()[0]

else:
	sys.stdout.write("Getting Blender sources\n")
	if not options.test:
		os.system("svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/blender")
os.chdir(working_directory)

# Update 'lib' on Windows
if PLATFORM == "win32":
	lib_dir= os.path.join(working_directory,'lib','windows')
	# if ARCH == '64bit':
	# 	lib_dir= os.path.join(working_directory,'lib','win64')
	if os.path.exists(lib_dir):
		os.chdir(lib_dir)
		if options.update:
			sys.stdout.write("Updating lib sources\n")
			if not options.test:
				os.system("svn update")
	else:
		# if ARCH == '64bit':
		# 	os.system("svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/win64 lib/win64")
		# else:
		sys.stdout.write("Getting lib sources\n")
		if not options.test:
			os.system("svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/windows lib/windows")
os.chdir(working_directory)

# Generate user settings file
sys.stdout.write("Generating user-config.py\n")
if not options.test:
	generate_user_config(os.path.join(blender_dir,'user-config.py'))

# Apply V-Ray/Blender patches if needed
patch_dir= os.path.join(working_directory,'vb25-patch')
if not options.pure_blender:
	if os.path.exists(patch_dir):
		os.chdir(patch_dir)
		if options.update_patch:
			sys.stdout.write("Updating vb25 patches\n")
			if not options.test:
				os.system("git pull")
	else:
		sys.stdout.write("Getting vb25 patches\n")
		if not options.test:
			os.system("git clone git://github.com/bdancer/vb25-patch.git")
	os.chdir(working_directory)

	if not options.test:
		shutil.copy(os.path.join(patch_dir, "splash.png.c"), os.path.join(blender_dir,"source","blender","editors","datafiles"))
		dst= os.path.join(blender_dir,"source","blender","exporter")
		if(os.path.exists(dst)):
			shutil.rmtree(dst)
		shutil.copytree(os.path.join(patch_dir, "exporter"), dst)
		os.system("patch -Np0 -i %s" % os.path.join(patch_dir,"vb25.patch"))

# Finally build Blender
sys.stdout.write("Building %s (%s)\n" % (project,REV))
if not options.test:
	os.chdir(blender_dir)
	build_cmd= "python scons/scons.py"
	if not PLATFORM == "win32":
		build_cmd= "sudo %s" % build_cmd
	if options.rebuild:
		os.system("%s clean" % build_cmd)
	if not options.rebuild:
		build_cmd+= " --implicit-deps-unchanged --max-drift=1"
	os.system(build_cmd)

# Generate docs if needed
if options.docs:
	if PLATFORM == "win32":
		sys.stdout.write("Docs generation on Windows is not supported\n")
	else:
		api_dir= os.path.join(install_dir,'api')
		sys.stdout.write("Generating docs: %s\n" % (api_dir))
		if not options.test:
			os.system("mkdir -p %s" % api_dir)
			os.system("sudo %s -b -P source/blender/python/doc/sphinx_doc_gen.py" % os.path.join(install_dir,'blender'))
			os.system("sudo sphinx-build source/blender/python/doc/sphinx-in %s" % api_dir)

# Set proper owner
if not PLATFORM == "win32":
	sys.stdout.write("Changing %s owner to %s:%s\n" % (install_dir,USER,USER))
	if not options.test:
		os.system("sudo chown -R %s:%s %s" % (USER,USER,install_dir))


# Generate archive (Linux) or installer (Windows)
if not options.debug and options.archive:
	archive_name= "%s-%s-ubuntu10_04-%s.tar.bz2" % (project,REV,ARCH)
	if PLATFORM == "win32":
		archive_name= "%s-%s-win32.exe" % (project,REV)
	sys.stdout.write("Creating release archive\n")
	sys.stdout.write("Adding vb25 exporter...\n")
	if not options.test:
		io_scripts_path= os.path.join(install_dir,'2.53','scripts','io')
		exporter_path= os.path.join(io_scripts_path,'vb25')
		os.chdir(io_scripts_path)
		if os.path.exists(exporter_path):
			os.chdir(exporter_path)
			if not options.test:
				os.system("git pull")
		else:
			if not options.test:
				os.system("git clone git://github.com/bdancer/vb25.git")

	if PLATFORM == "win32":
		sys.stdout.write("Generating installer: %s\n" % (archive_name))
	else:
		sys.stdout.write("Generating archive: %s\n" % (archive_name))
	if not options.test:
		if PLATFORM == "win32":
			generate_installer(patch_dir, install_dir, archive_name)
		else:
			os.chdir(install_dir)
			os.chdir('..')
			os.system("tar jcf %s %s" % (os.path.join(release_dir,archive_name),project))

notify("%s SVN update" % project, "Finished!")


