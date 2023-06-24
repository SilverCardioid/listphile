import argparse
import sys

from . import config_helpers as ch
from . import filelist

def _list_enum(e):
	return [x.name.lower() for x in e]

def main(test_args=None):
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(dest='action', required=True)
	options_parser = argparse.ArgumentParser(add_help=False)

	output_options = options_parser.add_argument_group('File output options')
	output_options.add_argument('--rel_to_cwd', '--cwd', action='store_true')
	output_options.add_argument('--append', action='store_true')
	output_options.add_argument('--header', default='')
	output_options.add_argument('--footer', default='')

	format_options = options_parser.add_argument_group('General format options')
	format_options.add_argument('--format-type', default='plain', type=str.lower, choices=_list_enum(ch.FormatType))
	format_options.add_argument('--start-level', type=int, default=0)
	format_options.add_argument('--max-depth', type=int, default=20)
	format_options.add_argument('--no-indent', dest='show_indent', action='store_false')
	format_options.add_argument('--indent', default=' ')
	format_options.add_argument('--show-ellipsis', action='store_false')
	format_options.add_argument('--ellipsis', default='...')
	format_options.add_argument('--newline', default='\n')

	filter_options = options_parser.add_argument_group('Sorting and filtering options')
	filter_options.add_argument('--no-folders', dest='show_folders', action='store_false')
	filter_options.add_argument('--no-files', dest='show_files', action='store_false')
	filter_options.add_argument('--filter-hidden', action='store_true')
	filter_options.add_argument('--item-grouping', default='filesfirst', type=str.lower, choices=_list_enum(ch.GroupType))

	prop_options = options_parser.add_argument_group('Item property format options')
	prop_options.add_argument('--name-type', default='name', type=str.lower, choices=_list_enum(ch.NameType))
	prop_options.add_argument('--root-name-type', default='dot', type=str.lower, choices=_list_enum(ch.NameType))
	prop_options.add_argument('--show-size', action='store_true')
	prop_options.add_argument('--show-date', action='store_true')
	prop_options.add_argument('--date-type', default='newest', type=str.lower, choices=_list_enum(ch.DateType))
	prop_options.add_argument('--date-format', default='%Y%m%d%H%M%S')
	prop_options.add_argument('--show-hash', action='store_true')
	prop_options.add_argument('--show-hidden', action='store_true')
	prop_options.add_argument('--hidden', default='*')

	list_parser = subparsers.add_parser('list', parents=[options_parser])
	list_parser.add_argument('folder', nargs='?', default='', help='Input folder.')
	list_parser.add_argument('--output', '-o', nargs='?', default=sys.stdout, const='filelist.txt', help='Output file path. If no value provided, use the default filename; if omitted entirely, print to the screen. Relative paths are with respect to the first input folder by default (see "rel_to_cwd").')

	if type(test_args) is str:
		test_args = test_args.split(' ')
	args = parser.parse_args(test_args)
	#print(args)

	if args.action == 'list':
		run_list(args)

def run_list(args):
	filelist.write_list(args.folder, args.output, args.__dict__)
