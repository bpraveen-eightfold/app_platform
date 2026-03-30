import os
import sys
import argparse
import shutil

def package(args):
	zip_name = os.path.join(args.write_path, args.package_name)
	shutil.make_archive(
		base_name=zip_name, 
		format='zip', 
		root_dir=os.getcwd(),
	)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--package_name', default='app_package', help='Name of your zip package')
    parser.add_argument('--write_path', default='../', help='Path where zip package will be written')

    args = parser.parse_args()

    package(args)

if __name__ == '__main__':
    main()

