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
				packages = "libspnav-dev build-essential gettext libxi-dev libsndfile1-dev libpng12-dev libfftw3-dev libopenjpeg-dev libopenal-dev libalut-dev libvorbis-dev libglu1-mesa-dev libsdl-dev libfreetype6-dev libtiff4-dev libjack-dev libx264-dev libmp3lame-dev git-core"
				if self.generate_docs:
					packages += " python-sphinx"
				sys.stdout.write("%s\n" % packages)
				os.system("sudo apt-get install %s" % packages)

			else:
				sys.stdout.write("Your distribution doesn't support automatic dependencies installation!\n")

			sys.exit(0)

		if self.build_deps:
			cmd = "sudo -E %s/install_deps.sh --source %s --install /opt" % (utils.path_join(self.dir_source, "vb25-patch"), utils.path_join(self.dir_source, "blender-deps"))

			if self.with_osl:
				cmd += " --with-llvm"
				cmd += " --with-osl"
			else:
				cmd += " --skip-llvm"
				cmd += " --skip-osl"

			if self.use_collada:
				cmd += " --with-opencollada"
			else:
				cmd += " --skip-opencollada"

			if self.build_release:
				cmd += " --all-static"

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

		if self.user_user_config:
			open(self.user_config, 'w').write(open(self.user_user_config, 'r').read())
			return

		build_options = {
			'WITH_VRAY_FOR_BLENDER' : self.add_patches or self.use_github_repo,

			'BF_DEBUG' : self.use_debug,

			'WITH_BF_FREESTYLE': False,
			'WITH_BF_CYCLES' : self.with_cycles,
			'WITH_BF_GAMEENGINE' : self.with_ge,
			'WITH_BF_PLAYER'     : self.with_player,
			'WITH_BF_COLLADA' : self.use_collada,

			'WITHOUT_BF_PYTHON_INSTALL' : not self.build_release,

			'WITH_BF_BULLET'          : True,
			'WITH_BF_FTGL'            : True,
			'WITH_BF_INTERNATIONAL'   : True,
			'WITH_BF_JPEG'            : True,
			'WITH_BF_OPENAL'          : True,
			'WITH_BF_OPENEXR'         : True,
			'WITH_BF_PNG'             : True,
			'WITH_BF_RAYOPTIMIZATION' : True,
			'WITH_BF_SDL'             : True,
			'WITH_BF_ZLIB'            : True,
			'WITH_BUILDINFO'          : True,

			'WITH_BF_FMOD'         : False,
			'WITH_BF_ICONV'        : False,
			'WITH_BF_QUICKTIME'    : False,
			'WITH_BF_STATICOPENGL' : False,
			'WITH_BF_FREESTYLE'    : False,
			'WITH_BF_VERSE'        : False,
		}

		if self.mode_developer:
			build_options['WITH_BF_CYCLES'] = False
			build_options['WITH_BF_OIIO'] = False
			build_options['WITH_BF_GAMEENGINE'] = False
			build_options['WITH_BF_PLAYER'] = False

		with open(self.user_config, 'w') as uc:
			uc.write("BF_INSTALLDIR = '%s'\n" % (self.dir_install_path))
			uc.write("BF_BUILDDIR = '/tmp/builder_%s'\n" % (self.build_arch))
			uc.write("BF_NUMJOBS = %i\n" % (self.build_threads))
			uc.write("\n")

			uc.write("WITH_BF_STATIC3DMOUSE = True\n")
			uc.write("\n")

			uc.write("WITH_BF_STATICPYTHON = True\n")
			uc.write("BF_PYTHON = '/opt/python-3.3'\n")
			uc.write("BF_PYTHON_ABI_FLAGS = 'm'\n")
			uc.write("\n")

			uc.write("WITH_BF_STATICFFMPEG = True\n")
			uc.write("BF_FFMPEG = '/opt/ffmpeg'\n")
			uc.write("BF_FFMPEG_LIBPATH='${BF_FFMPEG}/lib'\n")
			uc.write("BF_FFMPEG_LIB_STATIC = '${BF_FFMPEG_LIBPATH}/libavformat.a ${BF_FFMPEG_LIBPATH}/libavcodec.a ${BF_FFMPEG_LIBPATH}/libswscale.a ${BF_FFMPEG_LIBPATH}/libavutil.a ${BF_FFMPEG_LIBPATH}/libavdevice.a /usr/lib/x86_64-linux-gnu/libx264.a /usr/lib/x86_64-linux-gnu/libtheora.a'\n")
			uc.write("\n")

			uc.write("WITH_BF_OIIO = True\n")
			uc.write("WITH_BF_STATICOIIO = True\n")
			uc.write("BF_OIIO = '/opt/oiio'\n")
			uc.write("BF_OIIO_INC = '${BF_OIIO}/include'\n")
			uc.write("BF_OIIO_LIB = 'OpenImageIO'\n")
			uc.write("BF_OIIO_LIB_STATIC = '${BF_OIIO_LIBPATH}/libOpenImageIO.a /usr/lib/x86_64-linux-gnu/libjpeg.a'\n")
			uc.write("BF_OIIO_LIBPATH = '${BF_OIIO}/lib'\n")
			uc.write("\n")

			uc.write("WITH_BF_OCIO = True\n")
			uc.write("WITH_BF_STATICOCIO = True\n")
			uc.write("BF_OCIO = '/opt/ocio'\n")
			uc.write("BF_OCIO_INC = '${BF_OCIO}/include'\n")
			uc.write("BF_OCIO_LIB_STATIC = '${BF_OCIO_LIBPATH}/libOpenColorIO.a ${BF_OCIO_LIBPATH}/libtinyxml.a ${BF_OCIO_LIBPATH}/libyaml-cpp.a'\n")
			uc.write("BF_OCIO_LIBPATH = '${BF_OCIO}/lib'\n")
			uc.write("\n")
			
			uc.write("WITH_BF_STATICOPENEXR = True\n")
			uc.write("BF_OPENEXR = '/opt/openexr'\n")
			uc.write("BF_OPENEXR_INC = '${BF_OPENEXR}/include/OpenEXR'\n")
			uc.write("BF_OPENEXR_LIB_STATIC = '${BF_OPENEXR}/lib/libHalf.a ${BF_OPENEXR}/lib/libIlmImf-2_1.a ${BF_OPENEXR}/lib/libIex-2_1.a ${BF_OPENEXR}/lib/libImath-2_1.a ${BF_OPENEXR}/lib/libIlmThread-2_1.a'\n")
			uc.write("\n")

			uc.write("WITH_BF_BOOST = True\n")
			uc.write("WITH_BF_STATICBOOST = True\n")
			uc.write("BF_BOOST = '/opt/boost'\n")
			uc.write("BF_BOOST_INC = '/opt/boost/include'\n")
			uc.write("BF_BOOST_LIBPATH = '/opt/boost/lib'\n")
			uc.write("BF_BOOST_LIB_STATIC = '${BF_BOOST_LIBPATH}/libboost_regex.a ${BF_BOOST_LIBPATH}/libboost_date_time.a ${BF_BOOST_LIBPATH}/libboost_filesystem.a ${BF_BOOST_LIBPATH}/libboost_thread.a ${BF_BOOST_LIBPATH}/libboost_locale.a ${BF_BOOST_LIBPATH}/libboost_system.a'\n")
			uc.write("\n")

			# Write boolean options
			for key in build_options:
				uc.write("%s = %s\n" % (key, build_options[key]))


	def package(self):
		subdir = "linux" + "/" + self.build_arch

		release_path = os.path.join(self.dir_release, subdir)

		if not self.mode_test:
			utils.path_create(release_path)

		# Example: vrayblender-2.60-42181-Calculate-11.9-x86_64.tar.bz2
		archive_name = "%s-%s-%s-%s-%s-%s-%s-%s.tar.bz2" % (self.project, self.status, self.version, self.commits, self.revision, self.host_linux['short_name'], self.host_linux['version'], self.build_arch)
		archive_path = utils.path_join(release_path, archive_name)

		sys.stdout.write("Generating archive: %s\n" % (archive_name))
		sys.stdout.write("  in: %s\n" % (release_path))

		cmd = "tar jcf %s %s" % (archive_path, self.dir_install_name)

		sys.stdout.write("Calling: %s\n" % (cmd))
		sys.stdout.write("  in: %s\n" % (self.dir_install))

		if not self.mode_test:
			os.chdir(self.dir_install)
			os.system(cmd)

		return subdir, archive_path
