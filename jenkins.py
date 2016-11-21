#
# V-Ray For Blender jenkins Build Wrapper
#
# http://chaosgroup.com
#
# Author: Andrei Izrantcev
# E-Mail: andrei.izrantcev@chaosgroup.com
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
import re
import sys
import glob
import platform
import subprocess

from builder import utils

def setup_msvc_2013(cgrepo):
    env = {
        'INCLUDE' : [
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/shared",
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/um",
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/winrt",
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/ucrt",
            "{CGR_SDK}/msvs2013/include",
            "{CGR_SDK}/msvs2013/atlmfc/include",
        ],

        'LIB' : [
            "{CGR_SDK}/msvs2013/PlatformSDK/Lib/winv6.3/um/x64",
            "{CGR_SDK}/msvs2013/PlatformSDK/Lib/ucrt/x64",
            "{CGR_SDK}/msvs2013/atlmfc/lib/amd64",
            "{CGR_SDK}/msvs2013/lib/amd64",
        ],

        'PATH' : [
                "{CGR_SDK}/msvs2013/bin/amd64",
                "{CGR_SDK}/msvs2013/bin",
                "{CGR_SDK}/msvs2013/PlatformSDK/bin/x64",
            ] + os.environ['PATH'].split(os.pathsep)
        ,
    }
    os.environ['__MS_VC_INSTALL_PATH'] = "{CGR_SDK}/msvs2013"
    for var in env:
        os.environ[var] = ";".join(env[var]).format(CGR_SDK=cgrepo)


def get_appsdk(appsdk_name, appsdk_version, dir_source):
    appsdk_os_dir_name = {
        utils.WIN: 'windows',
        utils.LNX: 'linux',
        utils.MAC: 'darwin',
    }[utils.get_host_os()]

    vray_ext = 'exe' if utils.get_host_os() == utils.WIN else 'bin'

    all_appsdk_root = os.path.join(dir_source, 'vray-appsdk')

    # clean all non-needed files
    for item in glob.glob('%s/*' % all_appsdk_root):
        if re.match(r'^\d{8}$', item) is None:
            if os.path.isdir(item):
                utils.remove_path(item)

    appsdk_path = os.path.join(all_appsdk_root, appsdk_version, appsdk_os_dir_name)
    appsdk_check = os.path.join(appsdk_path, 'bin', 'vray.%s' % vray_ext)
    download_appsdk = not os.path.exists(appsdk_check)

    sys.stdout.write('Missing vray [%s]\n' % appsdk_check)
    sys.stdout.write('Creating dir [%s]\n' % appsdk_path)
    sys.stdout.flush()

    try:
        os.makedirs(appsdk_path)
    except:
        pass

    curl = 'curl -s -S -o %s ftp://%s:%s@nightlies.chaosgroup.com/vrayappsdk/%s/%s' % (
        appsdk_name,
        os.environ['NIGHTLIES_USER'],
        os.environ['NIGHTLIES_PASS'],
        appsdk_version,
        appsdk_name,
    )

    sys.stdout.write('Downloading appsdk:\n')
    sys.stdout.write('CURL [%s]\n' % curl)
    sys.stdout.flush()
    os.chdir(appsdk_path)
    os.system(curl)

    extract_cmds = {
        utils.WIN: ['7z x %s' % appsdk_name],
        utils.LNX: ['7z x %s' % appsdk_name],
        utils.MAC: ['7z x %s' % appsdk_name, 'mv *.tar appsdk.tar', '7z x appsdk.tar'],
    }[utils.get_host_os()]

    for cmd in extract_cmds:
        sys.stdout.write('Extract CMD [%s]\n' % cmd)
        sys.stdout.flush()
        os.system(cmd)

    tar_name = appsdk_name[0:-3]
    if utils.get_host_os() != utils.WIN and os.path.exists(os.path.join(appsdk_path, tar_name)):
        cmd = "7z x %s" % tar_name
        sys.stdout.write('Extract tar CMD [%s]\n' % cmd)
        sys.stdout.flush()
        os.system(cmd)

    utils.remove_path(os.path.join(appsdk_path, appsdk_name))
    return all_appsdk_root


def main(args):
    sys.stdout.write('jenkins args:\n%s\n' % str(args))
    sys.stdout.flush()

    dir_build = os.getcwd()
    os.environ['http_proxy'] = '10.0.0.1:1234'
    os.environ['https_proxy'] = '10.0.0.1:1234'
    os.environ['ftp_proxy'] = '10.0.0.1:1234'
    os.environ['socks_proxy'] = '10.0.0.1:1080'

    os.environ['http_proxy'] = 'http://10.0.0.1:1234/'
    os.environ['https_proxy'] = 'https://10.0.0.1:1234/'

    cgrepo = os.environ['VRAY_CGREPO_PATH']
    kdrive_os_dir_name = {
        utils.WIN: 'win',
        utils.LNX: 'linux',
        utils.MAC: 'mac',
    }[utils.get_host_os()]
    kdrive = os.path.join(cgrepo, 'sdk', kdrive_os_dir_name)

    if sys.platform == 'win32':
        setup_msvc_2013(kdrive)

    dir_source = os.path.join(args.jenkins_perm_path, 'blender-dependencies')
    if not os.path.exists(dir_source):
        os.makedirs(dir_source)

    branch = 'dev/vray_for_blender/%s' % args.jenkins_project_type

    ### GET APPSDK
    if args.jenkins_project_type == 'vb35':
        appsdk_remote_name = {
            utils.WIN: 'appsdk-win-qt-nightly-1.11.00-vray34501-20161110.7z',
            utils.LNX: 'appsdk-linux-qt-nightly-1.11.00-vray34501-20161110.tar.xz',
            utils.MAC: 'appsdk-mac-qt-nightly-1.11.00-vray34501-20161110.tar.xz',
        }[utils.get_host_os()]

        if args.jenkins_appsdk_remote_name != '':
            appsdk_remote_name = args.jenkins_appsdk_remote_name

        appsdk_version = re.match(r'.*?vray\d{5}-(\d{8})\.(?:tar\.xz|7z)*?', appsdk_remote_name).groups()[0]

        appsdk_path = get_appsdk(appsdk_remote_name, appsdk_version, dir_source)

        sys.stdout.write('CGR_APPSDK_PATH [%s], CGR_APPSDK_VERSION [%s]\n' % (appsdk_path, appsdk_version))
        os.environ['CGR_BUILD_TYPE'] = args.jenkins_build_type
        os.environ['CGR_APPSDK_PATH'] = appsdk_path
        os.environ['CGR_APPSDK_VERSION'] = appsdk_version

    ### ADD NINJA TO PATH
    ninja_path = 'None'
    if sys.platform == 'win32':
        ninja_path = os.path.join(cgrepo, 'build_scripts', 'cmake', 'tools', 'bin')
    else:
        ninja_path = os.path.join(os.environ['CI_ROOT'], 'ninja', 'ninja')
    sys.stdout.write('Ninja path [%s]\n' % ninja_path)
    sys.stdout.flush()
    os.environ['PATH'] = ninja_path + os.pathsep + os.environ['PATH']

    ### CLONE REPOS
    blender_modules = [
        "release/scripts/addons_contrib",
        "source/tools",
        "release/scripts/addons",
    ]

    if args.jenkins_project_type == 'vb35':
        blender_modules.append('intern/vray_for_blender_rt/extern/vray-zmq-wrapper')

    os.chdir(dir_source)
    utils.get_repo('git@github.com:bdancer/blender-for-vray', branch=branch, submodules=blender_modules, target_name='blender')
    utils.get_repo('git@github.com:ChaosGroup/blender-for-vray-libs')

    if args.jenkins_project_type == 'vb35':
        utils.get_repo('git@github.com:bdancer/vrayserverzmq', submodules=['extern/vray-zmq-wrapper'])

    if utils.get_host_os() == utils.MAC:
        boost_root = os.path.join(kdrive, 'boost', 'boost_1_61_0')

        mac_version_names = {
            "10.9": "mavericks",
            "10.8": "mountain_lion",
            "10.6": "snow_leopard",
        }

        mac_version = '.'.join(platform.mac_ver()[0].split('.')[0:2])
        mac_name = mac_version_names[mac_version] if mac_version in mac_version_names else None
        sys.stdout.write('Mac ver full [%s] -> %s == %s' % (str(platform.mac_ver()), mac_version, mac_name))

        boost_lib = os.path.join(boost_root, 'lib', '%s_x64' % mac_name)

        if not mac_name or not os.path.exists(boost_lib):
            sys.stderr.write('Boost path [%s] missing for this version of mac!\n' % boost_lib)
            sys.stderr.flush()

            mac_name = mac_version_names['10.9']
            boost_lib = os.path.join(boost_root, 'lib', '%s_x64' % mac_name)

            if not mac_name or not os.path.exists(boost_lib):
                sys.stderr.write('Boost path [%s] missing for this version of mac... exiting!\n' % boost_lib)
                sys.stderr.flush()
                sys.exit(1)
            else:
                sys.stderr.write('Trying to build with [%s] instead!\n' % boost_lib)
                sys.stderr.flush()

        boost_lib_dir = os.path.join(boost_lib, 'gcc-4.2-cpp')

        python_patch = os.path.join(dir_source, 'blender-for-vray-libs', 'Darwin', 'pyport.h')
        patch_steps = [
            "svn --non-interactive --trust-server-cert checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/darwin-9.x.universal lib/darwin-9.x.universal",
            "svn --non-interactive --trust-server-cert checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/win64_vc12 lib/win64_vc12",
            "cp -Rf lib/win64_vc12/opensubdiv/include/opensubdiv/* lib/darwin-9.x.universal/opensubdiv/include/opensubdiv/",
            "cp lib/darwin-9.x.universal/png/lib/libpng12.a lib/darwin-9.x.universal/png/lib/libpng.a",
            "cp lib/darwin-9.x.universal/png/lib/libpng12.la lib/darwin-9.x.universal/png/lib/libpng.la",
            "mkdir -p lib/darwin-9.x.universal/release/site-packages",
            "rm -rf lib/darwin-9.x.universal/boost_1_60",
            "mv lib/darwin-9.x.universal/boost lib/darwin-9.x.universal/boost_1_60",
            "mkdir -p lib/darwin-9.x.universal/boost/include",
            "cp -r %s/boost lib/darwin-9.x.universal/boost/include/boost" % boost_root,
            "cp -r %s lib/darwin-9.x.universal/boost/lib" % boost_lib_dir,
            "cp -f %s lib/darwin-9.x.universal/python/include/python3.5m/pyport.h" % python_patch,
        ]
        os.chdir(dir_source)

        for step in patch_steps:
            sys.stdout.write('MAC patch step [%s]\n' % step)
            sys.stdout.flush()
            os.system(step)

    os.chdir(dir_build)
    ### CLONE REPOS

    python_exe = sys.executable

    sys.stdout.write('jenkins args:\n%s\n' % str(args))
    sys.stdout.flush()

    cmd = [python_exe]
    cmd.append("vb25-patch/build.py")
    cmd.append("--jenkins")
    cmd.append('--dir_source=%s' % dir_source)
    cmd.append('--dir_build=%s' % dir_build)
    cmd.append("--teamcity_project_type=%s" % args.jenkins_project_type)

    cmd.append('--github-src-branch=%s' % branch)
    if args.jenkins_project_type == 'vb35':
        cmd.append('--teamcity_zmq_server_hash=%s' % utils.get_git_head_hash(os.path.join(dir_source, 'vrayserverzmq')))

    cmd.append('--jenkins_kdrive_path=%s' % kdrive)
    os.environ['jenkins_kdrive_path'] = kdrive
    cmd.append('--jenkins_output=%s' % args.jenkins_output)

    if utils.get_host_os() == utils.LNX:
        dir_blender_libs = os.path.join(dir_source, 'prebuilt-libs')
        if not os.path.exists(dir_blender_libs):
            sys.stdout.write('Missing prebuilt-libs path [%s], trying to create\n' % dir_blender_libs)
            sys.stdout.flush()
            os.makedirs(dir_blender_libs)
        cmd.append('--dir_blender_libs=%s' % dir_blender_libs)

    cmd.append('--build_clean')
    cmd.append('--with_ge')
    cmd.append('--with_player')
    cmd.append('--with_collada')
    if utils.get_host_os() == utils.WIN:
        cmd.append('--vc_2013')

    cmd.append('--build_mode=release')
    cmd.append('--build_type=%s' % args.jenkins_build_type)
    cmd.append('--use_package')
    cmd.append('--use_installer=CGR')
    cmd.append('--dir_cgr_installer=%s' % os.path.join(dir_source, 'blender-for-vray-libs', 'cgr_installer'))

    if args.jenkins_with_static_libc:
        cmd.append('--teamcity_with_static_libc')

    cmd.append('--dev_static_libs')

    cmd.append('--upblender=off')
    cmd.append('--uppatch=off')

    cmd.append('--gcc=gcc')
    cmd.append('--gxx=g++')

    cmd.append('--dir_install=%s' % os.path.join(args.jenkins_output, 'install', 'vray_for_blender'))
    cmd.append('--dir_release=%s' % os.path.join(args.jenkins_output, 'release', 'vray_for_blender'))

    sys.stdout.write('Calling builder:\n%s\n' % '\n\t'.join(cmd))
    sys.stdout.flush()

    return subprocess.call(cmd, cwd=dir_build)


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(usage="python3 jenkins.py [options]")


    parser.add_argument('--jenkins_output',
        default = "",
        required=True,
    )

    parser.add_argument('--jenkins_appsdk_remote_name',
        default = "",
        help='Remote name of the appsdk archive, examples: "appsdk-win-qt-nightly-1.09.00-vray33501-20160510.7z" OR "appsdk-linux-qt-nightly-1.09.00-vray33501-20160510.tar.xz" OR "appsdk-mac-qt-nightly-1.09.00-vray33501-20160510.tar.xz"',
    )

    parser.add_argument('--jenkins_perm_path',
        default = "",
        required=True,
    )

    parser.add_argument('--jenkins_project_type',
        choices=['vb30', 'vb35'],
        default = 'vb30',
        required=True,
    )

    parser.add_argument('--jenkins_with_static_libc',
        action = 'store_true',
    )

    parser.add_argument('--jenkins_build_type',
        choices=['debug', 'release'],
        default = 'Release',
        required=True,
    )

    args = parser.parse_args()

    sys.exit(main(args))
