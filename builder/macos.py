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


import os
import sys

from builder import utils
from builder import Builder


class MacBuilder(Builder):
	def config(self):
		sys.stdout.write("Generating build configuration:\n")
		sys.stdout.write("  in: %s\n" % (self.user_config))

		if self.mode_test:
			return

		if self.user_user_config:
			open(self.user_config, 'w').write(open(self.user_user_config, 'r').read())
			return

		uc= open(self.user_config, 'w')

		if self.use_debug:
			uc.write("BF_DEBUG    = True\n")

		uc.write("BF_INSTALLDIR = '%s'\n" % (self.dir_install_path))
		uc.write("BF_BUILDDIR   = '/tmp/builder_%s'\n" % (self.build_arch))
		uc.write("\n")

		uc.write("WITH_BF_PLAYER = False\n")
		uc.write("\n")

		# Cycles
		#
		if self.with_cycles:
			uc.write("WITH_BF_CYCLES       = True\n")
			uc.write("WITH_BF_OIIO         = True\n")
			uc.write("\n")

		uc.write("BF_QUIET    = True\n")
		uc.write("BF_NUMJOBS  = %s\n" % (self.build_threads))
		uc.write("\n")

		uc.write("MACOSX_ARCHITECTURE      = '%s'\n" % ('i386' if self.build_arch == 'x86' else 'x86_64'))
		uc.write("MAC_CUR_VER              = '%s'\n" % self.osx_sdk)
		uc.write("MAC_MIN_VERS             = '%s'\n" % self.osx_sdk)
		uc.write("MACOSX_DEPLOYMENT_TARGET = '%s'\n" % self.osx_sdk)
		uc.write("MACOSX_SDK               = '/Developer/SDKs/MacOSX%s.sdk'\n" % self.osx_sdk)
		uc.write("LCGDIR                   = '#../lib/darwin-9.x.universal'\n")
		uc.write("LIBDIR                   = '#../lib/darwin-9.x.universal'\n")

		uc.write("CC                       = 'gcc'\n")
		uc.write("CXX                      = 'g++'\n")

		uc.write("USE_SDK                  = True\n")
		uc.write("WITH_GHOST_COCOA         = True\n")
		uc.write("WITH_BF_QUICKTIME        = False\n")

		uc.write("ARCH_FLAGS = ['-arch', MACOSX_ARCHITECTURE]\n")

		uc.write("CFLAGS     = ['-pipe','-funsigned-char'] + ARCH_FLAGS\n")
		uc.write("CPPFLAGS   = [] + ARCH_FLAGS\n")
		uc.write("CCFLAGS    = ['-pipe','-funsigned-char'] + ARCH_FLAGS\n")
		uc.write("CXXFLAGS   = ['-pipe','-funsigned-char'] + ARCH_FLAGS\n")

		uc.write("SDK_FLAGS          = ['-isysroot', MACOSX_SDK, '-mmacosx-version-min='+MAC_MIN_VERS, '-arch', MACOSX_ARCHITECTURE]\n")
		uc.write("PLATFORM_LINKFLAGS = ['-fexceptions','-framework','CoreServices','-framework','Foundation','-framework','IOKit','-framework','AppKit','-framework','Cocoa','-framework','Carbon','-framework','AudioUnit','-framework','AudioToolbox','-framework','CoreAudio','-framework','OpenAL']+ARCH_FLAGS\n")
		uc.write("PLATFORM_LINKFLAGS = ['-mmacosx-version-min='+MAC_MIN_VERS, '-Wl', '-isysroot', MACOSX_SDK, '-arch', MACOSX_ARCHITECTURE] + PLATFORM_LINKFLAGS\n")
		uc.write("CCFLAGS  = SDK_FLAGS + CCFLAGS\n")
		uc.write("CXXFLAGS = SDK_FLAGS + CXXFLAGS\n")
		uc.write("REL_CFLAGS  = ['-DNDEBUG', '-O2','-ftree-vectorize','-msse','-msse2','-msse3','-mfpmath=sse']\n")
		uc.write("REL_CCFLAGS = ['-DNDEBUG', '-O2','-ftree-vectorize','-msse','-msse2','-msse3','-mfpmath=sse']\n")
		uc.write("REL_CFLAGS  = REL_CFLAGS + ['-march=core2','-mssse3','-with-tune=core2','-enable-threads']\n")
		uc.write("REL_CCFLAGS = REL_CCFLAGS + ['-march=core2','-mssse3','-with-tune=core2','-enable-threads']\n")

		uc.write("\n")
		uc.close()


	def package(self):
		release_path = utils.path_join(self.dir_release, "macos", self.build_arch)

		if not self.mode_test:
			utils.path_create(release_path)

		# Example: vrayblender-2.60-42181-macos-10.6-x86_64.tar.bz2
		archive_name = "%s-%s-%s-macos-%s-%s.tar.bz2" % (self.project, self.version, self.revision, self.osx_sdk, self.build_arch)
		archive_path = utils.path_join(release_path, archive_name)

		sys.stdout.write("Generating archive: %s\n" % (archive_name))
		sys.stdout.write("  in: %s\n" % (release_path))

		cmd = "tar jcf %s %s" % (archive_path, self.dir_install_name)

		sys.stdout.write("Calling: %s\n" % (cmd))
		sys.stdout.write("  in: %s\n" % (self.dir_install))

		if not self.mode_test:
			os.chdir(self.dir_install)
			os.system(cmd)
