from __future__ import annotations
from datetime import datetime
import os
import re
import string
import typing as ty

from . import config, paths

def _fmtdate(date_format:str, time:int) -> str:
	return datetime.fromtimestamp(time).strftime(date_format)

def _date_to_regex(date_format:str) -> str:
	return re.sub(r'%([A-Za-z%])', lambda m: '\d+?' if m[1] in 'wdmyYHIMSfjUWuV' else '%' if m[1] == '%' else '.+?',
	              re.escape(date_format))

_formatter = string.Formatter()

class Props(dict):
	#def __init__(self, **props):
	#	super().__init__(self, **props)

	def __repr__(self) -> str:
		return 'Props(' + super().__repr__() + ')'

	def get_depth(self, start_level:int = 0, *, indent:str = ' ') -> ty.Optional[int]:
		if 'depth' in self:
			return self['depth']
		if 'level' in self:
			return self['level'] - start_level
		if 'indent' in self and len(indent) > 0:
			return len(self['indent'])//len(indent) - start_level
		return None

	def get_name(self) -> ty.Optional[str]:
		if 'name' in self:
			return self['name']
		if 'relpath' in self:
			return os.path.basename(self['relpath'])
		return None

	def get_path(self, item_type:ty.Optional[str] = None, parents:ty.Optional[ty.List[str]] = None, *,
	             depth:ty.Optional[int] = None, start_level:int = 0, indent:str = ' ') -> ty.Optional[str]:
		# Get depth from properties, or else from argument (based on dir/dir_close)
		parsed_depth = self.get_depth(start_level, indent=indent)
		if parsed_depth is not None:
			depth = parsed_depth

		if 'relpath' in self:
			# Update parents & return relpath
			if parents is not None:
				parent = self['relpath'].split(os.sep) if depth > 0 else []
				if item_type in ('file', 'dir_close') and depth > 0:
					# remove filename or step out
					parent = parent[:(depth - 1)]
				parents[:] = parent
			return self['relpath']

		if parents is not None and depth is not None and 'name' in self:
			# Update parents & return parents + name
			# todo: can keep name for dir_close/ellipsis
			path = (parents[:(depth - 1)] + [self['name']] if depth > 0
				              else [])
			if item_type in ('file', 'dir_close'):
				# remove filename or step out
				parents[:] = path[:-1]
			else:
				parents[:] = path
			return os.path.join(*path) if len(path) > 0 else ''

			# parent = parents[:(depth - 1)]
			# if item_type == 'dir': # step in
				# parents[:] = (parent + [self['name']] if depth > 0
				              # else [])
			# elif item_type == 'dir_close': # step out
				# parents[:] = parent
			# return os.path.join(*parent, self['name'])

		# No name or parents
		return None


class Format:
	_get_property = {
		'indent'  : lambda item, options: options.indent*(item.depth + options.start_level),
		'level'   : lambda item, options: item.depth + options.start_level,
		'depth'   : lambda item, options: item.depth,
		'name'    : lambda item, options: item.abspath.parts[-1],
		'relpath' : lambda item, options: str(item.path),
		'abspath' : lambda item, options: str(item.abspath),
		'hidden'  : lambda item, options: options.hidden if item.hidden else '',
		'size'    : lambda item, options: item.data.st_size,
		'cdate'   : lambda item, options: _fmtdate(options.date_format, item.data.st_ctime),
		'mdate'   : lambda item, options: _fmtdate(options.date_format, item.data.st_mtime),
		'ndate'   : lambda item, options: _fmtdate(options.date_format, max(item.data.st_ctime, item.data.st_mtime)),
		'hash'    : lambda item, options: item.hash(),
	}
	_get_regex = {
		'indent'  : lambda options: '(?:' + re.escape(options.indent) + ')*',
		'level'   : lambda options: r'\d+?',
		'depth'   : lambda options: r'\d+?',
		'name'    : lambda options: r'[^\\\/:\*\?"<>\|]+?',
		'relpath' : lambda options: r'[^\*?"<>\|]+?',
		'abspath' : lambda options: r'[^\*?"<>\|]+?',
		'hidden'  : lambda options: '(?:' + re.escape(options.hidden) + ')?',
		'size'    : lambda options: r'\d+?',
		'cdate'   : lambda options: _date_to_regex(options.date_format),
		'mdate'   : lambda options: _date_to_regex(options.date_format),
		'ndate'   : lambda options: _date_to_regex(options.date_format),
		'hash'    : lambda options: r'[0-9a-f]+'
	}

	def __init__(self, pattern:str, options:config.Options):
		self.pattern = pattern
		self._options = options
		self.props_list = [field[1] for field in _formatter.parse(self.pattern) if field[1] is not None]
		if any(prop == '' or str.isdecimal(prop) for prop in self.props_list):
			raise ValueError("positional arguments not supported in format string")

		self.props = set(self.props_list)
		if options.properties:
			self.props |= set(options.properties)
		for prop in self.props:
			if prop not in self.__class__._get_property:
				raise ValueError(f'unknown property in pattern: {prop}')

		self.regex = re.compile('^' + re.sub(
			r'\\{(\w*)[^{}]*\\}',
			lambda m: '(' + (self.__class__._get_regex[m[1]](self._options)
			          if m[1] in self.__class__._get_regex else '.*?') + ')',
			re.escape(self.pattern)
		) + '$')

	def __repr__(self) -> str:
		return f'Format({self.pattern!r})'

	def __bool__(self) -> bool:
		return self.pattern != ''

	def _get_props(self, item:paths.PathItem, **overrides) -> Props:
		# Get property values, skipping overridden ones
		props = {k: self.__class__._get_property[k](item, self._options)
		         for k in self.props - set(overrides.keys())}
		if overrides:
			props.update(overrides)
		return Props(**props)

	def apply(self, item:paths.PathItem, **properties) -> str:
		props = self._get_props(item, **properties)
		return self.pattern.format(**props)

	def parse(self, string:str) -> ty.Optional[Props]:
		pts = re.match(self.regex, string)
		if pts:
			return Props(**{self.props_list[i]: val for i,val in enumerate(pts.groups())})
		else:
			return None

def add_property(key:str, getter:ty.Union[ty.Callable[[paths.PathItem,config.Options],ty.Any],ty.Any] = '',
                 regex:ty.Union[ty.Callable[[config.Options],str],str,None] = r'.*?'):
	Format._get_property[key] = getter if callable(getter) \
		else lambda item, options: getter
	Format._get_regex[key] = regex if callable(regex) \
		else lambda options: regex
