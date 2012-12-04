#
# V-Ray/Blender Build System
#
# http://vray.cgdo.ru
#
# Author: Andrey M. Izrantsev (aka bdancer)
# E-Mail: izrantsev@cgdo.ru
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.
#


import optparse
import os
import sys

import builder as build_system


host_os = build_system.utils.get_host_os()

parser = optparse.OptionParser(usage="python %prog [options]", version="2.0")

parser.add_option('', '--sourcedir',                         dest= 'sourcedir',                    help= "Source directory.", metavar= 'FILE')
parser.add_option('', '--installdir',                        dest= 'installdir',                   help= "Installation directory.", metavar= 'FILE')
parser.add_option('', '--builddir',                          dest= 'builddir',                     help= "Build directory.", metavar= 'FILE')
parser.add_option('', '--releasedir',                        dest= 'releasedir',                   help= "Directory for package (installer or archive).", metavar= 'FILE')
parser.add_option('', '--release',    action= 'store_true',  dest= 'release',     default= False,  help= "Release build.")
parser.add_option('', '--package',    action= 'store_true',  dest= 'package',     default= False,  help= "Create archive (Linux, Mac OS) or installer (Windows, NSIS required).")

# Blender options
parser.add_option('', '--collada',    action= 'store_true',  dest= 'collada',     default= False,  help= "Add OpenCollada support.")
parser.add_option('', '--player',     action= 'store_true',  dest= 'player',      default= False,  help= "Build Blender Player.")

# Updates
parser.add_option('', '--upblender',                         dest= 'upblender',   default= 'on',   help= "Update Blender sources.", type= 'choice', choices=('on', 'off'))
parser.add_option('', '--uppatch',                           dest= 'uppatch',     default= 'on',   help= "Update patch sources.", type= 'choice', choices=('on', 'off'))

# Building options
parser.add_option('', '--exporter_cpp',action= 'store_true', dest= 'exporter_cpp',default= False,  help= "Use new cpp exporter.")
parser.add_option('', '--with_cycles', action= 'store_true', dest= 'with_cycles', default= False,  help= "Add Cycles.")
parser.add_option('', '--debug_build', action= 'store_true', dest= 'debug',       default= False,  help= "Debug build.")
parser.add_option('', '--rebuild',     action= 'store_true', dest= 'rebuild',     default= False,  help= "Full rebuild.")
parser.add_option('', '--revision',                          dest= 'revision',    default= "",     help= "Checkout particular SVN revision.")
parser.add_option('', '--nopatches',   action= 'store_true', dest= 'nopatches',   default= False,  help= "Don't apply V-Ray/Blender patches.")
parser.add_option('', '--nodatafiles', action= 'store_true', dest= 'nodatafiles', default= False,  help= "Don't add splash screen.")
parser.add_option('', '--addextra',    action= 'store_true', dest= 'addextra',    default= False,  help= "Apply \"extra\" patches.")
parser.add_option('', '--optimize',    action= 'store_true', dest= 'optimize',    default= False,  help= "Use compiler optimizations.")
parser.add_option('', '--jobs',                              dest= 'jobs',        default= 4,      help= "Number of build threads.")
if host_os == build_system.utils.MAC:
	parser.add_option('', '--osx',                           dest= 'osx',         default= "10.6", help= "Mac OS X version.")
	parser.add_option('', '--osx_arch',                      dest= 'osx_arch',    default= "x86",  help= "Mac OS X architecture.", type= 'choice', choices=('x86', 'x86_64'))
if host_os == build_system.utils.LNX:
	parser.add_option('', '--deps',    action= 'store_true', dest= 'deps',        default= False,  help= "Install dependencies (Gentoo, OpenSuse, Fedora, Ubuntu).")
	parser.add_option('', '--docs',    action= 'store_true', dest= 'docs',        default= False,  help= "Build Python API documentation (python-sphinx required).")
	parser.add_option('', '--desktop', action= 'store_true', dest= 'desktop',     default= False,  help= "Generate .desktop file.")

# Script options
parser.add_option('', '--debug',     action= 'store_true', dest= 'mode_debug', default= False, help= "Script debug output.")
parser.add_option('', '--test',      action= 'store_true', dest= 'mode_test',  default= False, help= "Test mode.")
parser.add_option('', '--developer', action= 'store_true', dest= 'mode_devel', default= False, help= optparse.SUPPRESS_HELP) # Special mode used only by me =)

parser.add_option('', '--use_deps_script', action='store_true', dest='use_deps_script', default=False, help="Use BF deps build script")


(options, args) = parser.parse_args()


params = {}

# Assuming current directory as source directory by default
params['dir_source']     = os.getcwd()
if options.sourcedir:
	params['dir_source'] = build_system.utils.path_slashify(options.sourcedir)

# Default build directory
if host_os == build_system.utils.WIN:
	# Its vital to use short path here like C:\b\
	params['dir_build'] = "C:\\b\\"
else:
	params['dir_build'] = "/tmp/builder/"

if options.builddir:
	params['dir_build'] = build_system.utils.path_slashify(options.builddir)

if options.installdir:
	params['dir_install'] = build_system.utils.path_slashify(options.installdir)

if options.releasedir:
	params['dir_release'] = build_system.utils.path_slashify(options.releasedir)

params['update_blender'] = True if options.upblender == 'on' else False
params['update_patch']   = True if options.uppatch == 'on' else False

params['generate_package'] = options.package

params['use_debug']  = options.debug

params['build_release']  = options.release
params['build_threads']  = int(options.jobs)

params['mode_debug']     = options.mode_debug
params['mode_developer'] = options.mode_devel
params['mode_test']      = options.mode_test

params['add_datafiles']  = not options.nodatafiles
params['add_extra']      = options.addextra

params['exporter_cpp']   = options.exporter_cpp

if host_os == build_system.utils.LNX:
	params['generate_docs']  = options.docs
	params['install_deps']   = options.deps

if host_os == build_system.utils.MAC:
	params['build_arch'] = options.osx_arch

# Just for sure to disable debug for release build
if params['build_release']:
	params['use_debug'] = False

# Just for sure to disable 'Developer' mode if OS is not Linux
if host_os != build_system.utils.LNX:
	params['mode_developer'] = False

if options.revision:
	params['checkout_revision'] = options.revision

params['with_cycles'] = options.with_cycles

params['use_deps_script'] = options.use_deps_script

builder = build_system.Builder(params)
builder.build()
