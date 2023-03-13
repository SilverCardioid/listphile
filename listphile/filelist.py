from __future__ import annotations
import os
from pathlib import Path
import typing as ty

from . import config, format, paths

class FileLister:
	def __init__(self, **options):
		self.options = config.Options()
		self.options.__dict__.update(options)
		self.set_formats()
		self._key = None

	def set_formats(self, *, file_format:ty.Optional[str] = None,
	                dir_format:ty.Optional[str] = None,
	                dir_close_format:ty.Optional[str] = None,
	                root_format:ty.Optional[str] = None,
	                ellipsis_format:ty.Optional[str] = None):
		fmt_args = config._Formats(
			file=file_format, dir=dir_format, dir_close=dir_close_format,
			root=root_format, ellipsis=ellipsis_format)
		for item_type in config.ITEM_TYPES:
			fmt_attr = item_type + '_format'
			# Get input argument
			fmt_string = getattr(fmt_args, item_type)
			if fmt_string is not None:
				# Update options
				setattr(self.options, fmt_attr, fmt_string)
			else:
				# Get or construct format from options
				fmt_string = self.options._get_format(item_type)
			# Create Format object (or keep None)
			fmt = fmt_string and format.Format(fmt_string, self.options)
			# Set self.file_format, etc.
			setattr(self, fmt_attr, fmt)

	def dir_function(self, item:paths.PathItem, args:ty.Optional[dict] = None):
		if item.depth == 0 and self.root_format and \
		   args and 'file' in args:
			line = self.root_format.apply(item)
			args['file'].write(line)
		elif item.depth > 0 and self.dir_format and \
		     args and 'file' in args:
			line = self.dir_format.apply(item)
			args['file'].write(line)

	def file_function(self, item:paths.PathItem, args:ty.Optional[dict] = None):
		if self.file_format and args and 'file' in args:
			line = self.file_format.apply(item)
			args['file'].write(line)

	def ellipsis_function(self, item:paths.PathItem, args:ty.Optional[dict] = None):
		if self.ellipsis_format and args and 'file' in args:
			line = self.ellipsis_format.apply(item)
			args['file'].write(line)

	def dir_close_function(self, item:paths.PathItem, args:ty.Optional[dict] = None):
		if self.dir_close_format and args and 'file' in args:
			line = self.dir_close_format.apply(item)
			args['file'].write(line)

	def write_list(self, folder:ty.Union[paths.PathOrStr,ty.Sequence[paths.PathOrStr]] = '', list_path:paths.PathOrStr = ''):
		if isinstance(folder, (Path, str, None)):
			base_folders = [folder]
		else: # sequence
			base_folders = folder

		list_path = paths._parse_path(list_path)
		if not list_path.is_absolute():
			if self.options.rel_to_cwd: # Save location relative to CWD rather than base folder
				list_path = list_path.absolute()
			else: # Save location relative to first target folder
				list_path = (base_folders[0] / list_path).absolute()
		if list_path.is_dir():
			list_path /= 'filelist' + self.options._get_default_extension()

		list_file = None
		try:
			list_file = open(str(list_path), 'a' if self.options.append else 'w', encoding='utf-8')
			if self.options.header:
				list_file.write(self.options.header)

			for folder in base_folders:
				abs_folder = paths._parse_path(folder).absolute()
				self.run_folder(abs_folder, args={'file': list_file})

			if self.options.footer:
				list_file.write(self.options.footer)

		finally:
			if list_file and not list_file.closed:
				list_file.close()

	def run_folder(self, folder:paths.PathOrStr = '', *,
	              args:ty.Optional[dict] = None, _item:ty.Optional[paths.PathItem] = None):
		item = _item
		if item is None:
			folder = paths._parse_path(folder)
			assert folder.is_dir()
			item = paths.PathItem(folder.absolute(), isdir=True)
			self._key = self.options._get_key()

		self.dir_function(item, args=args)

		if self.options.max_depth and item.depth >= self.options.max_depth:
			# write ellipsis without visiting folder
			self.ellipsis_function(item, args=args)

		else:
			child_items = item.children(self._key)
			for child_item in child_items:
				if self.options._is_filtered(child_item):
					continue
				if child_item.isdir:
					self.run_folder(_item=child_item, args=args)
				else:
					self.file_function(child_item, args=args)

		self.dir_close_function(item, args=args)


	def generate(self, folder:paths.PathOrStr = '', *, _item:ty.Optional[paths.PathItem] = None
	             ) -> ty.Generator[ty.Tuple[str, Path, format.Props], None, None]:
		item = _item
		if item is None:
			folder = paths._parse_path(folder)
			assert folder.is_dir()
			item = paths.PathItem(folder.absolute(), isdir=True)
			self._key = self.options._get_key()

		if self.dir_format:
			props = self.dir_format._get_props(item)
			yield ('dir', item.path, props)

		if self.options.max_depth and item.depth >= self.options.max_depth:
			# write ellipsis without visiting folder
			if self.ellipsis_format:
				props = self.ellipsis_format._get_props(item)
				yield ('ellipsis', item.path, props)

		else:
			child_items = item.children(key=self._key)
			for child_item in child_items:
				if self.options._is_filtered(child_item):
					continue
				if child_item.isdir:
					yield from self.generate(_item=child_item)
				elif self.file_format:
					props = self.file_format._get_props(child_item)
					yield ('file', child_item.path, props)

		if self.dir_close_format:
			props = self.dir_close_format._get_props(item)
			yield ('dir_close', item.path, props)


	def parse_list(self, list_path:paths.PathOrStr) -> ty.Generator[ty.Tuple[str, Path, ty.Optional[format.Props]], None, None]:
		# todo: match header/footer
		depth_from_hierarchy = self.dir_format is not None and self.dir_close_format is not None
		with open(str(list_path), 'r', encoding='utf-8') as list_file:
			parents = []
			depth = 0 if depth_from_hierarchy else None
			for line in list_file:
				matches = []
				# folder?
				pts = self.dir_format and self.dir_format.parse(line)
				if pts is not None:
					matches.append(('dir', pts))
					if depth_from_hierarchy: depth += 1
				# file?
				pts = self.file_format and self.file_format.parse(line)
				if pts is not None:
					matches.append(('file', pts))
				# folder close?
				pts = self.dir_close_format and self.dir_close_format.parse(line)
				if pts is not None:
					matches.append(('dir_close', pts))
					if depth_from_hierarchy: depth -= 1
				# ellipsis?
				pts = self.ellipsis_format and self.ellipsis_format.parse(line)
				if pts is not None:
					matches.append(('ellipsis', pts))

				if len(matches) == 0:
					print(f'Failed to parse line: {line.strip()}')
					continue
				elif len(matches) > 1:
					match_types = '/'.join(m[0] for m in matches)
					print(f'Ambiguous line/format: {line.strip()} ({match_types})')

				item_type, pts = matches[0]
				full_path = Path(pts.get_path(item_type, parents, depth=depth, start_level=self.options.start_level))
				yield (item_type, full_path, pts)


def write_list(folder:ty.Union[paths.PathOrStr,ty.Sequence[paths.PathOrStr]] = '', list_path:paths.PathOrStr = '',
	           options:ty.Optional[dict] = None):
	FileLister(**(options or {})).write_list(folder, list_path)

def generate(folder:paths.PathOrStr = '', options:ty.Optional[dict] = None
             ) -> ty.Generator[ty.Tuple[str, Path, format.Props], None, None]:
	yield from FileLister(**(options or {})).generate(folder)

def parse_list(list_path:paths.PathOrStr, options:ty.Optional[dict] = None
               ) -> ty.Generator[ty.Tuple[str, Path, format.Props], None, None]:
	yield from FileLister(**(options or {})).parse_list(list_path)
