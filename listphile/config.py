from __future__ import annotations
import typing as ty

from . import paths
from .config_helpers import (
	FormatType, DateType, NameType, GroupType, _enum_equals,
	_SortKey, grouped_sort_key, group_sort_key, DEFAULTSORT, GROUPED_DEFAULTSORT)

class Options:
	rel_to_cwd      : bool = False
	append          : bool = False
	header          : str  = ''
	footer          : str  = ''

	format_type     : ty.Union[FormatType,str] = FormatType.PLAIN
	dir_format      : ty.Optional[str]         = None
	dir_close_format: ty.Optional[str]         = None
	root_format     : ty.Optional[str]         = None
	file_format     : ty.Optional[str]         = None
	ellipsis_format : ty.Optional[str]         = None

	start_level     : int                     = 0
	max_depth       : ty.Optional[int]        = 20
	name_type       : ty.Union[NameType,str]  = NameType.NAME
	root_name_type  : ty.Union[NameType,str]  = NameType.DOT
	item_grouping   : ty.Union[GroupType,str] = GroupType.FILESFIRST
	sort_key        : ty.Optional[_SortKey]   = None

	show_folders    : bool                   = True
	show_files      : bool                   = True
	show_indent     : bool                   = True
	indent          : str                    = ' '
	newline         : str                    = '\n'
	show_size       : bool                   = False
	show_date       : bool                   = False
	date_type       : ty.Union[DateType,str] = DateType.NEWEST
	date_format     : str                    = '%Y%m%d%H%M%S'
	show_hash       : bool                   = False
	show_ellipsis   : bool                   = False
	ellipsis        : str                    = '...'
	show_hidden     : bool                   = False
	hidden          : str                    = '*'

	filter          : ty.Optional[ty.Callable[[paths.PathItem],bool]] = None
	filter_hidden   : bool                                            = False

	def _get_format(self, value:ty.Optional[str], toggle:bool, default:str) -> ty.Optional[str]:
		if value:
			return value
		elif value is None and toggle:
			return default
		else: # value == '' or not toggle
			return None

	def _get_date_prop(self, val:ty.Union[DateType,str]) -> ty.Tuple[str, bool]:
		if _enum_equals(val, DateType.NEWEST):
			return ('ndate', False)
		if _enum_equals(val, DateType.CREATION):
			return ('cdate', False)
		if _enum_equals(val, DateType.MODIFICATION):
			return ('mdate', False)
		raise ValueError(f'unknown DateType value: {val}')

	def _get_name_prop(self, val:ty.Union[NameType,str]) -> ty.Tuple[str, bool]:
		if _enum_equals(val, NameType.DOT):
			return '.', True
		if _enum_equals(val, NameType.NAME):
			return 'name', False
		if _enum_equals(val, NameType.RELPATH):
			return 'relpath', False
		if _enum_equals(val, NameType.ABSPATH):
			return 'abspath', False
		raise ValueError(f'unknown NameType value: {val}')

	def _get_formats(self):
		if _enum_equals(self.format_type, FormatType.XML):
			return self._format_xml()
		else:
			return self._format_plain()

	def _format_list(self, formats, conditions):
		# [fmt1 if cond1,fmt2 if cond2,...]
		if any(conditions):
			items = [fmt for fmt,cond in zip(formats, conditions) if cond]
			return ' [' + ','.join(items) + ']'
		else:
			return ''

	def _format_plain(self):
		date_prop, date_lit = self._get_date_prop(self.date_type)
		name_prop, name_lit = self._get_name_prop(self.name_type)
		root_prop, root_lit = self._get_name_prop(self.root_name_type)
		date_fmt = date_prop if date_lit else f'{{{date_prop}}}'
		name_fmt = name_prop if name_lit else f'{{{name_prop}}}'
		root_fmt = root_prop if root_lit else f'{{{root_prop}}}'

		dir_format = self._get_format(
			self.dir_format, self.show_folders,
			('{indent}' if self.show_indent else '')
			+ '<' + name_fmt + ('{hidden}' if self.show_hidden else '') + '>'
			+ self.newline)
		root_format = self._get_format(
			self.root_format, self.show_folders,
			('{indent}' if self.show_indent else '')
			+ '<' + root_fmt + ('{hidden}' if self.show_hidden else '') + '>'
			+ self.newline)
		file_format = self._get_format(
			self.file_format, self.show_files,
			('{indent}' if self.show_indent else '')
			+ name_fmt + ('{hidden}' if self.show_hidden else '')
			+ self._format_list(('{size}', date_fmt, '{hash}'),
			                    (self.show_size, self.show_date, self.show_hash))
			+ self.newline)
		ellipsis_format = self._get_format(
			self.ellipsis_format, self.show_ellipsis,
			('{indent}' if self.show_indent else '')
			+ self.ellipsis + self.newline)
		dir_close_format = self._get_format(self.dir_close_format, False, '')

		return dir_format, file_format, root_format, ellipsis_format, dir_close_format


	def _format_xml(self):
		date_prop, date_lit = self._get_date_prop(self.date_type)
		name_prop, name_lit = self._get_name_prop(self.name_type)
		root_prop, root_lit = self._get_name_prop(self.root_name_type)
		date_fmt = '' if date_lit else f' {date_prop}="{{{date_prop}}}"'
		name_fmt = '' if name_lit else f' {name_prop}="{{{name_prop}}}"'
		root_fmt = '' if root_lit else f' {name_prop}="{{{root_prop}}}"'

		dir_format = self._get_format(
			self.dir_format, self.show_folders,
			('{indent}' if self.show_indent else '')
			+ '<Folder' + name_fmt
			+ (' hidden="{hidden}"' if self.show_hidden else '') + '>'
			+ self.newline)
		root_format = self._get_format(
			self.root_format, self.show_folders,
			('{indent}' if self.show_indent else '')
			+ '<Folder' + root_fmt
			+ (' hidden="{hidden}"' if self.show_hidden else '') + '>'
			+ self.newline)
		file_format = self._get_format(
			self.file_format, self.show_files,
			('{indent}' if self.show_indent else '')
			+ '<File' + name_fmt
			+ (' hidden="{hidden}"' if self.show_hidden else '')
			+ (' size="{size}"' if self.show_size else '')
			+ (date_fmt if self.show_date else '')
			+ (' hash="{hash}"' if self.show_size else '') + '/>'
			+ self.newline)
		ellipsis_format = self._get_format(
			self.ellipsis_format, self.show_ellipsis,
			('{indent}' if self.show_indent else '')
			+ '<Ellipsis/>' + self.newline)
		dir_close_format = self._get_format(
			self.dir_close_format, self.show_folders,
			('{indent}' if self.show_indent else '')
			+ '</Folder>' + self.newline)

		return dir_format, file_format, root_format, ellipsis_format, dir_close_format

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
