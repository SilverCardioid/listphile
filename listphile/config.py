from __future__ import annotations
import collections
import typing as ty

from . import paths
from .config_helpers import (
	FormatType, DateType, NameType, GroupType, _get_enum, _enum_equals,
	_SortKey, _group_keys, grouped_sort_key, group_sort_key, join_keys,
	DEFAULTSORT, GROUPED_DEFAULTSORT)

class Options:
	rel_to_cwd      : bool = False
	append          : bool = False
	header          : str  = ''
	footer          : str  = ''

	file_format     : ty.Optional[str] = None
	dir_format      : ty.Optional[str] = None
	dir_close_format: ty.Optional[str] = None
	root_format     : ty.Optional[str] = None
	ellipsis_format : ty.Optional[str] = None

	format_type     : ty.Union[FormatType,str]      = FormatType.PLAIN
	start_level     : int                           = 0
	max_depth       : ty.Optional[int]              = 20
	show_indent     : bool                          = True
	indent          : str                           = ' '
	newline         : str                           = '\n'
	properties      : ty.Optional[ty.Iterable[str]] = None

	show_folders    : bool                                            = True
	show_files      : bool                                            = True
	filter          : ty.Optional[ty.Callable[[paths.PathItem],bool]] = None
	filter_hidden   : bool                                            = False
	item_grouping   : ty.Union[GroupType,str]                         = GroupType.FILESFIRST
	sort_key        : ty.Optional[_SortKey]                           = None

	name_type       : ty.Union[NameType,str] = NameType.NAME
	root_name_type  : ty.Union[NameType,str] = NameType.DOT
	show_size       : bool                   = False
	show_date       : bool                   = False
	date_type       : ty.Union[DateType,str] = DateType.NEWEST
	date_format     : str                    = '%Y%m%d%H%M%S'
	show_hash       : bool                   = False
	show_ellipsis   : bool                   = False
	ellipsis        : str                    = '...'
	show_hidden     : bool                   = False
	hidden          : str                    = '*'

	def _get_format(self, item_type:str) -> ty.Optional[str]:
		format_type = _get_enum(FormatType, self.format_type)
		return _get_format_string[format_type][item_type](self)

	def _get_key(self) -> _SortKey:
		sort_key = self.sort_key or DEFAULTSORT
		group_key = _group_keys[_get_enum(GroupType, self.item_grouping)]
		return join_keys(group_key, sort_key)

	def _get_default_extension(self) -> str:
		if self.format_type and _enum_equals(self.format_type, FormatType.XML):
			return '.xml'
		return '.txt'

	def _is_filtered(self, item:paths.PathItem) -> bool:
		if self.filter_hidden and item.hidden:
			return True
		if self.filter is not None and self.filter(item):
			return True
		return False

## Format construction

ITEM_TYPES = ['file', 'dir', 'dir_close', 'root', 'ellipsis']
_Formats = collections.namedtuple('Formats', ITEM_TYPES)

def _toggle_format(value:ty.Optional[str], toggle:bool,
                   default:str) -> ty.Optional[str]:
	if value: # explicit format
		return value
	elif value is None and toggle: # automatic format
		return default
	else: # value == '' or not toggle: omit
		return None

def _toggle_concat(sep:str, items:ty.Sequence[ty.Tuple[bool,str]]) -> str:
	return sep.join((string or '') for toggle, string in items if toggle)

_date_props = {
	FormatType.PLAIN: {
		DateType.NEWEST      : '{ndate}',
		DateType.CREATION    : '{cdate}',
		DateType.MODIFICATION: '{mdate}'
	},
	FormatType.XML: {
		DateType.NEWEST      : ' ndate="{ndate}"',
		DateType.CREATION    : ' cdate="{cdate}"',
		DateType.MODIFICATION: ' mdate="{mdate}"'
	}
}
def _get_date_prop(format_type:FormatType,
                   date_type:ty.Union[DateType,str]) -> str:
	return _date_props[format_type][_get_enum(DateType, date_type)]

_name_props = {
	FormatType.PLAIN: {
		NameType.DOT    : '.',
		NameType.NAME   : '{name}',
		NameType.RELPATH: '{relpath}',
		NameType.ABSPATH: '{abspath}'
	},
	FormatType.XML: {
		NameType.DOT    : '',
		NameType.NAME   : ' name="{name}"',
		NameType.RELPATH: ' relpath="{relpath}"',
		NameType.ABSPATH: ' abspath="{abspath}"'
	}
}
def _get_name_prop(format_type:FormatType,
                   name_type:ty.Union[NameType,str]) -> str:
	return _name_props[format_type][_get_enum(NameType, name_type)]

_get_format_string = {
	FormatType.PLAIN: {
		'file':      lambda opt: _toggle_format(
			opt.file_format, opt.show_files,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, _get_name_prop(FormatType.PLAIN, opt.name_type)),
				(opt.show_hidden, '{hidden}'),
				(opt.show_size or opt.show_date or opt.show_hash,
				 ' [' + _toggle_concat(',', [
					(opt.show_size, '{size}'),
					(opt.show_date, _get_date_prop(FormatType.PLAIN, opt.date_type)),
					(opt.show_hash, '{hash}')
				 ]) + ']'),
				(True, opt.newline)
			])),
		'dir':       lambda opt: _toggle_format(
			opt.dir_format, opt.show_folders,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '<' + _get_name_prop(FormatType.PLAIN, opt.name_type)),
				(opt.show_hidden, '{hidden}'),
				(True, '>'),
				(True, opt.newline)
			])),
		'dir_close': lambda opt: _toggle_format(
			opt.dir_close_format, False, ''),
		'root':      lambda opt: _toggle_format(
			opt.root_format, opt.show_folders,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '<' + _get_name_prop(FormatType.PLAIN, opt.root_name_type)),
				(opt.show_hidden, '{hidden}'),
				(True, '>'),
				(True, opt.newline)
			])),
		'ellipsis':  lambda opt: _toggle_format(
			opt.ellipsis_format, opt.show_ellipsis,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, opt.ellipsis),
				(True, opt.newline)
			]))
	},
	FormatType.XML: {
		'file':      lambda opt: _toggle_format(
			opt.file_format, opt.show_files,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '<File' + _get_name_prop(FormatType.XML, opt.name_type)),
				(opt.show_hidden, ' hidden="{hidden}"'),
				(opt.show_size, ' size="{size}"'),
				(opt.show_date, _get_date_prop(FormatType.XML, opt.date_type)),
				(opt.show_hash, ' hash="{hash}"'),
				(True, '/>'),
				(True, opt.newline)
			])),
		'dir':       lambda opt: _toggle_format(
			opt.dir_format, opt.show_folders,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '<Folder' + _get_name_prop(FormatType.XML, opt.name_type)),
				(opt.show_hidden, ' hidden="{hidden}"'),
				(True, '>'),
				(True, opt.newline)
			])),
		'dir_close': lambda opt: _toggle_format(
			opt.dir_close_format, opt.show_folders,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '</Folder>'),
				(True, opt.newline)
			])),
		'root':      lambda opt: _toggle_format(
			opt.root_format, opt.show_folders,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '<Folder' + _get_name_prop(FormatType.XML, opt.root_name_type)),
				(opt.show_hidden, ' hidden="{hidden}"'),
				(True, '>'),
				(True, opt.newline)
			])),
		'ellipsis':  lambda opt: _toggle_format(
			opt.ellipsis_format, opt.show_ellipsis,
			_toggle_concat('', [
				(opt.show_indent, '{indent}'),
				(True, '<Ellipsis/>'),
				(True, opt.newline)
			]))
	}
}
