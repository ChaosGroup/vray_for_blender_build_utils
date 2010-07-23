import os
import string
import glob
import shutil
import sys
import subprocess

from optparse import OptionParser

parser = OptionParser()

parser.add_option("-t", "--test",
                  action="store_true", dest="test", default=False,
                  help="don't create installer")

(options, args) = parser.parse_args()

# Globals
PLATFORM= "win32"
BF_PYTHON_VERSION= "2.6.4"

INSTALLER_DIR= "C:\\release\\installer"
if not os.path.exists(INSTALLER_DIR):
	os.makedirs(INSTALLER_DIR)

def create_installer(VERSION, with_vray= None, test= None):
		if test:
			print "Generating installer: V-Ray/Blender %s"%(VERSION),
			if with_vray:
				print "with VRay..."
			else:
				print "..."

		INSTALLER_NAME= "vrayblender-%s-%s.exe"%(VERSION, PLATFORM)
		if(with_vray):
			INSTALLER_NAME= "vrayblender-%s-%s-vray.exe"%(VERSION, PLATFORM)

		BF_INSTALLDIR= "C:\\release\\vrayblender-%s"%(VERSION)

		SKIP_DIRS= ('plugins')

		VRAY_DISTDIR= "C:\\release\\vray"
		VRAY_INSTDIR= "$INSTDIR\\vray"

		VDIRS= ['', 'plugins', 'plugins\DTE_Components']

		DIR= os.getcwd()


		# sciprt template
		ns = open("template.nsi","r")
		ns_cnt = str(ns.read())
		ns.close()


		ns_cnt = string.replace(ns_cnt, "[PYTHON_VERSION]", BF_PYTHON_VERSION)


		#
		# Add V-Ray section
		#
		vray_str= ""

		if(with_vray):
			vray_str+= "Section \"Install V-Ray Standalone Demo\" SectionVRay\n"

			vray_files= []
			vray_file_str= ""
			for vdir in VDIRS:
				vray_str+= '  SetOutPath \"%s\\%s\"\n'%(VRAY_INSTDIR, vdir)

				vray_dir= os.path.join(VRAY_DISTDIR, vdir)
				for vfile in os.listdir(vray_dir):
					vray_file= os.path.join(vray_dir, vfile)
					vray_file_str+= '  Delete $INSTDIR\\%s\n'%(os.path.join(vdir,vfile))
					if os.path.isdir(vray_file) == 0:
						vray_str+= '  File \"%s\"\n'%(vray_file)
				vray_str+= '\n'

			vray_str+= "  FileOpen  $9 \"$INSTDIR\\vray\\vrayconfig.xml\" w\n"
			vray_str+= "  FileWrite $9 \"<VRayStd>$\\r$\\n\"\n"
			vray_str+= "  FileWrite $9 \"  <Configuration>$\\r$\\n\"\n"
			vray_str+= "  FileWrite $9 \"    <PluginsPath>$INSTDIR\\vray\\plugins</PluginsPath>$\\r$\\n\"\n"
			vray_str+= "  FileWrite $9 \"  </Configuration>$\\r$\\n\"\n"
			vray_str+= "  FileWrite $9 \"</VRayStd>$\\r$\\n\"\n"
			vray_str+= "  FileClose $9\n"
			vray_str+= "SectionEnd\n"

			VDIRS.reverse()
			for vdir in VDIRS:
				vray_file_str+= '  RMDir /r %s\\%s\n'%(VRAY_INSTDIR, vdir)

		ns_cnt= string.replace(ns_cnt, "[VRAYSECTION]", vray_str)


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
		if(with_vray):
			delrootstring += vray_file_str

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

		if not test:
			os.system("makensis \"%s\""%(inst_nsis))


VERSIONS= ('2.49.12', '2.5')

create_installer('2.49.12',0,0)
