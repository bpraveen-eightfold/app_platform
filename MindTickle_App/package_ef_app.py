# pylint:disable=print-statement

from __future__ import absolute_import

import os
import argparse
import shutil
import subprocess
import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def install_dependencies():
    if not os.path.isfile('./requirements.txt'):
        print(bcolors.WARNING + 'Warning: requirements.txt not detected!' + bcolors.ENDC)
        return

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', './requirements.txt', '-t', './', '--upgrade'])
    print(bcolors.OKGREEN + 'Success: pip modules installed!' + bcolors.ENDC)

def package(project_path, package_name, write_path):
    zip_name = os.path.join(write_path, package_name)
    shutil.make_archive(
        base_name=zip_name, 
        format='zip', 
        root_dir=project_path,
    )

    print(bcolors.OKGREEN + 'Success: app package created at {}{}.zip{}'.format(bcolors.UNDERLINE, zip_name, bcolors.ENDC) + bcolors.ENDC)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--project_path', default=os.getcwd(), help='Path where your project is located')
    parser.add_argument('--package_name', default='app_package', help='Name of your zip package')
    parser.add_argument('--write_path', default='../', help='Path where zip package will be written')
    parser.add_argument('--skip_dependencies', action='store_true', help='Should dependencies be installed')

    args = parser.parse_args()
    if not args.skip_dependencies:
        install_dependencies()

    package(args.project_path, args.package_name, args.write_path)

if __name__ == '__main__':
    main()
