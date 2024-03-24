import argparse
import sys

#from . import compare
from . import config_helpers as ch
from . import filelist

def _list_enum(e):
	return [x.name.lower() for x in e]

def main(test_args=None):
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(dest='action', required=True)
	options_parser = argparse.ArgumentParser(add_help=False)

	output_options = options_parser.add_argument_group('File output options')
	output_options.add_argument('--rel-to-cwd', '--cwd', action='store_true', help='Treat a relative path for -o with respect to the current working directory instead of the input folder.')
	output_options.add_argument('--append', action='store_true', help='Append to the output file instead of overwriting it.')
	output_options.add_argument('--header', default='', help='Text to be printed before the file list.')
	output_options.add_argument('--footer', default='', help='Text to be printed after the file list.')

	format_options = options_parser.add_argument_group('General format options')
	format_options.add_argument('--format-type', '-f', default='plain', type=str.lower, choices=_list_enum(ch.FormatType), help='Format family to use. (default: %(default)s)')
	format_options.add_argument('--start-level', type=int, default=0, help='Indentation level for the root folder. (default: %(default)s)')
	format_options.add_argument('--max-depth', '-d', type=int, default=20, help='Maximum depth for folder traversal. 0 for unlimited depth. (default: %(default)s)')
	format_options.add_argument('--no-indent', dest='show_indent', action='store_false', help='Omit line indentation.')
	format_options.add_argument('--indent', default=' ', help='String used for indentation. (default: "%(default)s")')
	format_options.add_argument('--show-ellipsis', action='store_true', help='Mark items deeper than max_depth by an ellipsis.')
	format_options.add_argument('--ellipsis', default='...', help='String used for ellipsis lines in the plain layout. (default: "%(default)s")')
	#format_options.add_argument('--newline', default='\n', help='String printed between lines.')

	filter_options = options_parser.add_argument_group('Sorting and filtering options')
	filter_options.add_argument('--no-folders', dest='show_folders', action='store_false', help='Exclude directories.')
	filter_options.add_argument('--no-files', dest='show_files', action='store_false', help='Exclude files.')
	filter_options.add_argument('--filter-hidden', action='store_true', help='Exclude hidden files.')
	filter_options.add_argument('--item-grouping', default='filesfirst', type=str.lower, choices=_list_enum(ch.GroupType), help='Set the relative order of child folders and files. (default: %(default)s)')

	prop_options = options_parser.add_argument_group('Item property format options')
	prop_options.add_argument('--name-type', default='name', type=str.lower, choices=_list_enum(ch.NameType), help='How to display item names. (default: %(default)s)')
	prop_options.add_argument('--root-name-type', default='dot', type=str.lower, choices=_list_enum(ch.NameType), help='How to display the root folder. (default: %(default)s)')
	prop_options.add_argument('--show-size', '--size', action='store_true', help='Display file sizes.')
	prop_options.add_argument('--show-date', '--date',  action='store_true', help='Display file dates.')
	prop_options.add_argument('--date-type', default='newest', type=str.lower, choices=_list_enum(ch.DateType), help='The type of date to display. (default: %(default)s)')
	prop_options.add_argument('--date-format', default='%Y%m%d%H%M%S', help='The date format in `datetime.strftime` syntax. (default: "%(default)s")')
	prop_options.add_argument('--show-hash', '--hash', action='store_true', help='Display the SHA-1 hash for files.')
	prop_options.add_argument('--show-hidden', action='store_true', help='Mark hidden files.')
	prop_options.add_argument('--hidden', default='*', help='String used for marking hidden files. (default: "%(default)s")')

	list_parser = subparsers.add_parser('list', parents=[options_parser])
	list_parser.add_argument('folder', nargs='?', default='', help='Input folder.')
	list_parser.add_argument('--output', '-o', nargs='?', default=sys.stdout, const='filelist.txt', help='Output file path. If no value provided, use the default filename; if omitted entirely, print to the screen. Relative paths are with respect to the first input folder by default (see --rel-to-cwd).')

	#compare_parser = subparsers.add_parser('compare', parents=[options_parser])
	#compare_parser.add_argument('source1', default='filelist.txt')
	#compare_parser.add_argument('source2', default='')
	#compare_parser.add_argument('--output', '-o', nargs='?', default=sys.stdout, const='comparison.txt')

	if type(test_args) is str:
		test_args = test_args.split(' ')
	args = parser.parse_args(test_args)
	#print(args)

	if args.action == 'list':
		run_list(args)
	elif args.action == 'compare':
		run_compare(args)

def run_list(args):
	filelist.write_list(args.folder, args.output, args.__dict__)

def run_compare(args):
	raise NotImplementedError()
