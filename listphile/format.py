from __future__ import annotations
from datetime import datetime
import os
import re
import typing as ty

from . import config, paths

def _fmtdate(date_format:str, time:int) -> str:
	return datetime.fromtimestamp(time).strftime(date_format)

def _date_to_regex(date_format:str) -> str:
	return re.sub(r'%([A-Za-z%])', lambda m: '\d+?' if m[1] in 'wdmyYHIMSfjUWuV' else '%'if m[1] == '%' else '.+?',
	              re.escape(date_format))


class Props(dict):
	def __init__(self, **props):
		super().__init__(self, **props)

	def get_depth(self, start_level:int = 0) -> ty.Optional[int]:
		if 'depth' in self:
			return self['depth']
		if 'level' in self:
			return self['level'] - start_level
		if 'indent' in self:
			return len(self['indent']) - start_level
		return None

	def get_name(self) -> ty.Optional[str]:
		if 'name' in self:
			return self['name']
		if 'relpath' in self:
			return os.path.basename(self['relpath'])
		return None

	def get_path(self, item_type:ty.Optional[str] = None, parents:ty.Optional[ty.List[str]] = None, *,
	             depth:ty.Optional[int] = None, start_level:int = 0) -> ty.Optional[str]:
		if 'relpath' in self:
			# Update parents & return relpath
			if item_type == 'dir' and parents is not None:
				parents[:] = (self['relpath'].split(os.sep) if self['relpath'] != '.'
				              else [])
			return self['relpath']
		if parents is not None:
			parsed_depth = self.get_depth(start_level)
			if parsed_depth is None and depth is not None:
				# Use provided depth (based on dir/dir_close)
				parsed_depth = depth
			elif parsed_depth is None:
				# Unable to get depth; return name
				return self.get('name', None)
			# Update parents & return parents + name
			if 'name' in self:
				if item_type == 'dir':
					parents[:] = (parents[:(parsed_depth - 1)] + [self['name']] if parsed_depth > 0
					              else [])
				return os.path.join(*parents[:(parsed_depth - 1)], self['name'])
		# No name or parents
		return None


class Format:
	_get_property = {
		'indent'  : lambda item, options: options.indent*(item.depth + options.start_level),
		'level'   : lambda item, options: item.depth + options.start_level,
		'depth'   : lambda item, options: item.depth,
		'name'    : lambda item, options: item.path.parts[-1] if len(item.path.parts) > 0 else str(item.path),
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
		'hidden'  : lambda options: re.escape(options.hidden),
		'size'    : lambda options: r'\d+?',
		'cdate'   : lambda options: _date_to_regex(options.date_format),
		'mdate'   : lambda options: _date_to_regex(options.date_format),
		'ndate'   : lambda options: _date_to_regex(options.date_format),
		'hash'    : lambda options: r'[0-9a-f]+'
	}

	def __init__(self, pattern:str, options:config.Options):
		self.pattern = pattern
		self._options = options
		self.props_list = re.findall('{([^{}]+)}', self.pattern)
		self.props = set(self.props_list)
		self.regex = re.compile('^' + re.sub(
			r'\\{([^{}]+)\\}',
			lambda m: '(' + (self.__class__._get_regex[m[1]](self._options)
			          if m[1] in self.__class__._get_regex else '.*?') + ')',
			re.escape(self.pattern)
		) + '$')
		for prop in self.props:
			if prop not in self.__class__._get_property:
				raise ValueError(f'unknown property in pattern: {prop}')

	def __bool__(self):
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
