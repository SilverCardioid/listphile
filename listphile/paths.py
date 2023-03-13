from __future__ import annotations
import hashlib
import os
from pathlib import Path
import stat
import typing as ty

from . import config_helpers as ch

PathOrStr = ty.Union[Path, str, None]
def _parse_path(path:PathOrStr) -> Path:
	if not path:
		return Path('.')
	if isinstance(path, Path):
		return path
	return Path(path)

class PathItem:
	def __init__(self, basefolder:ty.Optional[Path] = None, path:ty.Optional[Path] = None,
	             *, depth:int = 0, isdir:bool = False):
		self.basefolder = basefolder or Path('').absolute()
		self.path = path or Path('')
		self.depth = depth
		self.isdir = isdir
		self._data = None

	@property
	def name(self) -> str:
		return self.path.name or self.basefolder.name

	@property
	def abspath(self) -> Path:
		return self.basefolder / self.path

	@property
	def data(self) -> os.stat_result:
		if self._data is None:
			self._data = self.abspath.stat()
		return self._data

	@property
	def hidden(self) -> bool:
		# https://stackoverfllow.com/questions/284115/cross-platform-hidden-file-detection
		return bool(self.data.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)

	def hash(self, *, buffer_size:int = 1024*1024, max_size:ty.Optional[int] = None) -> str:
		if self.abspath.is_file() and (not max_size or max_size <= self.data.st_size):
			hasher = hashlib.sha1()
			with open(self.abspath, 'rb') as file:
				while True:
					buf = file.read(buffer_size)
					if not buf: break
					hasher.update(buf)
			return hasher.hexdigest()
		else:
			return ''

	def get_name(self, name_type:ty.Union[ch.NameType,str] = ch.NameType.NAME) -> str:
		if ch._enum_equals(name_type, ch.NameType.DOT):
			return '.'
		elif ch._enum_equals(name_type, ch.NameType.NAME):
			return self.name
		elif ch._enum_equals(name_type, ch.NameType.RELPATH):
			return str(self.path)
		elif ch._enum_equals(name_type, ch.NameType.ABSPATH):
			return str(self.abspath)
		else:
			raise ValueError(f'unknown NameType value: {name_type}')

	def _child(self, name:str, isdir:bool = False) -> PathItem:
		return PathItem(self.basefolder, self.path / name, depth=self.depth + 1, isdir=isdir)

	def iterdir(self) -> ty.Generator[PathItem,None,None]:
		if self.abspath.is_dir():
			try:
				for child in self.abspath.iterdir():
					yield self._child(child.name, child.is_dir())
			except PermissionError: # system directory
				pass

	def children(self, key:ty.Optional[ch._SortKey] = None) -> ty.List[PathItem]:
		if not key: key = ch.GROUPED_DEFAULTSORT
		items = list(self.iterdir())
		items.sort(key=key)
		return items
