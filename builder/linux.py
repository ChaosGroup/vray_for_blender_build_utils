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


class LinuxBuilder(Builder):
	def post_init(self):
		if self.install_deps:
			sys.stdout.write("Installing dependencies: ")

			if self.host_linux['short_name'] == 'ubuntu':
				packages = "libspnav-dev subversion build-essential gettext libxi-dev libsndfile1-dev libpng12-dev libfftw3-dev libopenexr-dev libopenjpeg-dev libopenal-dev libalut-dev libvorbis-dev libglu1-mesa-dev libsdl-dev libfreetype6-dev libtiff4-dev libsamplerate0-dev libavdevice-dev libavformat-dev libavutil-dev libavcodec-dev libjack-dev libswscale-dev libx264-dev libmp3lame-dev python3.2-dev git-core libnotify-bin"
				if self.generate_docs:
					packages += " python-sphinx"
				packages += " libboost1.48-dev libboost-locale1.48-dev"
				sys.stdout.write("%s\n" % packages)
				os.system("sudo apt-get install %s" % packages)

			elif self.host_linux['short_name']  == 'opensuse':
				packages = "scons gcc-c++ xorg-x11-devel Mesa-devel xorg-x11-libs zlib-devel libpng-devel xorg-x11 libjpeg-devel freetype2-devel libtiff-devel OpenEXR-devel SDL-devel openal-devel fftw3-devel libsamplerate-devel libjack-devel python3-devel libogg-devel libvorbis-devel freealut-devel update-desktop-files libtheora-devel subversion git-core gettext-tools"
				sys.stdout.write("%s\n" % packages)
				os.system("sudo zypper install %s" % packages)

			elif self.host_linux['short_name']  == 'redhat' or self.host_linux['short_name']  == 'fedora':
				packages = "gcc-c++ subversion libpng-devel libjpeg-devel libXi-devel openexr-devel openal-soft-devel freealut-devel SDL-devel fftw-devel libtiff-devel lame-libs libsamplerate-devel freetype-devel jack-audio-connection-kit-devel ffmpeg-libs ffmpeg-devel xvidcore-devel libogg-devel faac-devel faad2-devel x264-devel libvorbis-devel libtheora-devel lame-devel python3 python3-devel python3-libs git-core"
				sys.stdout.write("%s\n" % packages)
				os.system("sudo yum install %s" % packages)

			elif self.host_linux['short_name']  == 'archlinux':
				#spacenavd
				packages = "desktop-file-utils ffmpeg fftw freetype2 hicolor-icon-theme libgl libxi mesa openal openimageio python"
				sys.stdout.write("%s\n" % packages)
				os.system("pacman -Sy %s" % packages)

			# elif self.host_linux['short_name']  == 'gentoo':
			# 	sys.stdout.write("Not supported yet :(\n")

			else:
				sys.stdout.write("Your distribution doesn't support automatic dependencies installation.\n")

			sys.exit(0)

		if self.build_deps:
			os.chdir(self.dir_blender_svn)
			cmd = "sudo ./build_files/build_environment/install_deps.sh --source %s --install /opt" % (utils.path_join(self.dir_source, "blender-deps"))

			if self.with_osl:
				cmd += "  --with-osl"

			if self.build_release:
				cmd += "  --all-static"

			if self.mode_test:
				print cmd
			else:
				os.system(cmd)

				os.system('sudo sh -c \"echo \"/opt/boost/lib\" > /etc/ld.so.conf.d/boost.conf\"')
				os.system('sudo ldconfig')

			sys.exit(0)


	def config(self):
		sys.stdout.write("Generating build configuration:\n")
		sys.stdout.write("  in: %s\n" % (self.user_config))

		if self.mode_test:
			return

		uc = open(self.user_config, 'w')

		build_options= {
			'True': [
				'WITH_BF_INTERNATIONAL',
				'WITH_BF_JPEG',
				'WITH_BF_PNG',
				'WITH_BF_OPENAL',
				'WITH_BF_SDL',
				'WITH_BF_BULLET',
				'WITH_BF_ZLIB',
				'WITH_BF_FTGL',
				'WITH_BF_RAYOPTIMIZATION',
				'WITH_BUILDINFO',
				'WITH_BF_OPENEXR',
			],
			'False': [
				'WITH_BF_ICONV',
				'WITH_BF_QUICKTIME',
				'WITH_BF_FMOD',
				'WITH_BF_STATICOPENGL',
				'WITH_BF_VERSE',
				'WITH_BF_PLAYER',
			]
		}

		if self.mode_developer:
			build_options['False'].append('WITH_BF_CYCLES')
			build_options['False'].append('WITH_BF_OIIO')
			build_options['False'].append('WITH_BF_GAMEENGINE')
		else:
			build_options['True'].append('WITH_BF_GAMEENGINE')
			if not self.with_cycles:
				build_options['False'].append('WITH_BF_CYCLES')
				build_options['False'].append('WITH_BF_OIIO')
			else:
				if self.with_cuda:
					build_options['True'].append('WITH_BF_CYCLES_CUDA_BINARIES')
					uc.write("BF_CYCLES_CUDA_BINARIES_ARCH = [%s]\n" % (','.join([ '"%s"'%(a) for a in self.cuda_gpu.split(',')])))

		if self.use_collada:
			build_options['True'].append('WITH_BF_COLLADA')
		else:
			build_options['False'].append('WITH_BF_COLLADA')

		if self.use_debug:
			build_options['True'].append('BF_DEBUG')

		uc.write("BF_INSTALLDIR = '%s'\n" % (self.dir_install_path))
		uc.write("BF_BUILDDIR   = '/tmp/builder_%s'\n" % (self.build_arch))
		uc.write("\n")

		uc.write("BF_OPENAL_LIB = 'openal alut'\n")
		uc.write("\n")

		if self.use_build_deps:
			uc.write("BF_PYTHON = '/opt/python-3.3'\n")
			uc.write("BF_PYTHON_ABI_FLAGS = 'm'\n")
			uc.write("BF_OCIO = '/opt/ocio'\n")
			uc.write("BF_OIIO = '/opt/oiio'\n")
			uc.write("BF_BOOST = '/opt/boost'\n")

			uc.write("BF_FFMPEG = '/opt/ffmpeg'\n")
			uc.write("BF_FFMPEG_LIB = 'avformat avcodec swscale avutil avdevice theoraenc theora theoradec vorbisenc vorbisfile vorbis x264 openjpeg'\n")

			uc.write("WITH_BF_STATICFFMPEG = False\n")
			#BF_FFMPEG_LIBPATH = '/opt/ffmpeg/lib'
			#BF_FFMPEG_LIB_STATIC = '${BF_FFMPEG_LIBPATH}/libavcodec.a ${BF_FFMPEG_LIBPATH}/libavdevice.a ${BF_FFMPEG_LIBPATH}/libavfilter.a ${BF_FFMPEG_LIBPATH}/libavformat.a ${BF_FFMPEG_LIBPATH}/libavutil.a ${BF_FFMPEG_LIBPATH}/libswresample.a ${BF_FFMPEG_LIBPATH}/libswscale.a'

			if self.build_release:
				uc.write("WITH_BF_OIIO = True\n")
				uc.write("WITH_BF_STATICOIIO = True\n")
				uc.write("BF_OIIO_LIBPATH = '${BF_OIIO}/lib'\n")
				uc.write("BF_OIIO_LIB_STATIC = '${BF_OIIO_LIBPATH}/libOpenImageIO.a'\n")

				uc.write("WITH_BF_BOOST = True\n")
				uc.write("WITH_BF_STATICBOOST = True\n")
				uc.write("BF_BOOST_INC = '/opt/boost/include'\n")
				uc.write("BF_BOOST_LIBPATH = '/opt/boost/lib'\n")
				uc.write("BF_BOOST_LIB_STATIC = '${BF_BOOST_LIBPATH}/libboost_regex.a ${BF_BOOST_LIBPATH}/libboost_date_time.a ${BF_BOOST_LIBPATH}/libboost_filesystem.a ${BF_BOOST_LIBPATH}/libboost_system.a ${BF_BOOST_LIBPATH}/libboost_thread.a ${BF_BOOST_LIBPATH}/libboost_locale.a'\n")
			else:
				uc.write("WITHOUT_BF_PYTHON_INSTALL = True\n")

		else:
			# Python settings
			#
			libpath = "/usr/lib"
			if self.host_linux['short_name'] == 'opensuse':
				libpath = "/usr/lib64"

			python_version = "3.2"
			python_suffix  = utils.python_get_suffix("/usr/include/python", python_version)

			uc.write("BF_PYTHON_VERSION    = '%s'\n" % (python_version))
			uc.write("BF_PYTHON            = '/usr'\n")
			uc.write("BF_PYTHON_LIBPATH    = '%s'\n" % (libpath))
			uc.write("BF_PYTHON_BINARY     = '/usr/bin/python%s'\n" % (python_version))
			uc.write("BF_PYTHON_INC        = '/usr/include/python%s%s'\n" % (python_version,python_suffix))
			uc.write("BF_PYTHON_LIB        = 'python%s%s'\n" % (python_version,python_suffix))
			uc.write("BF_PYTHON_LINKFLAGS  = ['-Xlinker', '-export-dynamic']\n")
			uc.write("BF_PYTHON_LIB_STATIC = '/usr/lib/libpython%s%s.a'\n" % (python_version,python_suffix))

			# Since blender is linked over external python
			# we don't need to embed it
			uc.write("WITHOUT_BF_PYTHON_INSTALL = True\n")
			uc.write("\n")
		uc.write("\n")

		# uc.write("BF_QUIET = False\n")
		uc.write("BF_TWEAK_MODE = False\n")
		uc.write("BF_NUMJOBS = %i\n" % (self.build_threads))

		uc.write("\n")

		# Write boolean options
		for key in build_options:
			for opt in build_options[key]:
				uc.write("{0:25} = {1}\n".format(opt, key))

		uc.write("\n")

		uc.write("C_WARN  = [\'-Wno-char-subscripts\', \'-Wdeclaration-after-statement\']\n")
		uc.write("CC_WARN = [\'-Wall\']\n")

		# Optimize for Intel Core
		if self.build_optimize:
			if self.build_optimize_type == 'INTEL':
				uc.write("CCFLAGS  = ['-pipe','-fPIC','-march=core2','-msse3','-mmmx','-mfpmath=sse','-funsigned-char','-fno-strict-aliasing','-ftracer','-fomit-frame-pointer','-finline-functions','-ffast-math']\n")
				uc.write("CXXFLAGS = CCFLAGS\n")
				uc.write("REL_CFLAGS  = ['-O3','-fomit-frame-pointer','-funroll-loops']\n")
				uc.write("REL_CCFLAGS = REL_CFLAGS\n")
		else:
			uc.write("CCFLAGS  = ['-pipe','-fPIC','-funsigned-char','-fno-strict-aliasing']\n")
			uc.write("CPPFLAGS = ['-DXP_UNIX']\n")
			uc.write("CXXFLAGS = CCFLAGS\n")
			uc.write("REL_CFLAGS  = ['-O2']\n")
			uc.write("REL_CCFLAGS = REL_CFLAGS\n")

		uc.close()


	def package(self):
		release_path = os.path.join(self.dir_release, "linux", self.build_arch)

		if not self.mode_test:
			utils.path_create(release_path)

		# Example: vrayblender-2.60-42181-Calculate-11.9-x86_64.tar.bz2
		archive_name = "%s-%s-%s-%s-%s-%s.tar.bz2" % (self.project, self.version, self.revision, self.host_linux['short_name'], self.host_linux['version'], self.build_arch)
		archive_path = utils.path_join(release_path, archive_name)

		sys.stdout.write("Generating archive: %s\n" % (archive_name))
		sys.stdout.write("  in: %s\n" % (release_path))

		cmd = "tar jcf %s %s" % (archive_path, self.dir_install_name)

		sys.stdout.write("Calling: %s\n" % (cmd))
		sys.stdout.write("  in: %s\n" % (self.dir_install))

		if not self.mode_test:
			os.chdir(self.dir_install)
			os.system(cmd)
