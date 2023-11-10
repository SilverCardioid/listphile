import os
from pathlib import Path
import typing as ty

from . import config_helpers as ch
from . import format, filelist, paths
from .filelist import ListItem

class DiffItem(ty.NamedTuple):
	diff_type:str
	item_type:str
	path:Path
	old_props:ty.Optional[format.Props] = None
	new_props:ty.Optional[format.Props] = None

class FileListComparer(filelist.FileLister):
	def compare(self, old_list:paths.PathOrStr, new_list:paths.PathOrStr = '.', *,
				skip_children:bool = False, names_only:bool = True
	            ) -> ty.Generator[DiffItem, None, None]:
		old_gen = self._get_gen(old_list)
		new_gen = self._get_gen(new_list)
		empty_item = ListItem(None, None, None)

		old = next(old_gen, empty_item)
		new = next(new_gen, empty_item)

		while old.item_type is not None or new.item_type is not None:
			diff = self._compare_lines(old, new)
			if diff == 0:
				assert old.path == new.path
				if (old.item_type == 'file' and not names_only and
				    not self._compare_files(old.props, new.props)):
					yield DiffItem('change', new.item_type, new.path, old.props, new.props)
				else:
					yield DiffItem('match', new.item_type, new.path, old.props, new.props)
				old = next(old_gen, empty_item)
				new = next(new_gen, empty_item)

			elif diff < 0:
				yield DiffItem('deletion', old.item_type, old.path, old.props, None)

				can_skip_children = False
				if skip_children and old.item_type == 'dir':
					old_dir_depth = self._get_depth(old.props)
					if old_dir_depth is not None:
						can_skip_children = True
				old = next(old_gen, empty_item)
				while can_skip_children and old.props and self._get_depth(old.props) > old_dir_depth:
					old = next(old_gen, empty_item)

			else:
				yield DiffItem('addition', new.item_type, new.path, None, new.props)

				can_skip_children = False
				if skip_children and new.item_type == 'dir':
					new_dir_depth = self._get_depth(new.props)
					if new_dir_depth is not None:
						can_skip_children = True
				new = next(new_gen, empty_item)
				while can_skip_children and new.props and self._get_depth(new.props) > new_dir_depth:
					new = next(new_gen, empty_item)

	def _get_depth(self, props:format.Props) -> ty.Optional[int]:
		return props.get_depth(start_level=self.options.start_level, indent=self.options.indent)

	def _compare_lines(self, old:ListItem, new:ListItem) -> int:
		# positive result -> addition (old list ahead, new line missing in old list)
		# list that hasn't run out yet -> missing in other list
		if old.item_type is None or new.item_type is None:
			return (old.item_type is None) - (new.item_type is None)
		# higher indent -> missing in other list
		old_depth, new_depth = self._get_depth(old.props), self._get_depth(new.props)
		if old_depth is not None and new_depth is not None:
			if old_depth != new_depth:
				return -old_depth + new_depth
			if (old.item_type == 'dir' and new.item_type == 'dir' and
			    old_depth == new_depth == 0):
				# root folders always match
				return 0
		# child file before child folder (or vice versa) -> missing in other list
		old_isdir, new_isdir = 'dir' in old.item_type, 'dir' in new.item_type
		item_grouping = ch._get_enum(ch.GroupType, self.options.item_grouping)
		if item_grouping != ch.GroupType.MIXED:
			if item_grouping == ch.GroupType.FILESFIRST:
				isdir_diff = old_isdir - new_isdir
			else:
				isdir_diff = -old_isdir + new_isdir
			if isdir_diff != 0:
				return isdir_diff
		# alphabetically first -> missing in other list
		old_name = old.props.get_name()
		new_name = new.props.get_name()
		if old_name is not None and new_name is not None:
			if self.options.sort_key:
				# todo: base folder?
				old_name = self.options.sort_key(paths.PathItem(None, old.path, old_depth or 0, old_isdir))
				new_name = self.options.sort_key(paths.PathItem(None, new.path, new_depth or 0, new_isdir))
			return (new_name < old_name) - (old_name < new_name)
		return 0


	def _compare_files(self, old_props:format.Props, new_props:format.Props) -> bool:
		# Return whether two files match based on their properties
		if 'hash' in old_props and 'hash' in new_props:
			return old_props['hash'] == new_props['hash']
		if 'size' in old_props and 'size' in new_props and old_props['size'] != new_props['size']:
			return False
		if 'mdate' in old_props and 'mdate' in new_props:
			return old_props['mdate'] == new_props['mdate']
		if 'ndate' in old_props and 'ndate' in new_props:
			return old_props['ndate'] == new_props['ndate']
		return True

	def _get_gen(self, list_or_folder:paths.PathOrStr
	             ) -> ty.Generator[ListItem, None, None]:
		if os.path.isdir(list_or_folder):
			return self.generate(list_or_folder)
		elif os.path.isfile(list_or_folder):
			return self.parse_list(list_or_folder)
		else:
			raise FileNotFoundError(list_or_folder)

def compare(old_list:paths.PathOrStr, new_list:paths.PathOrStr = '.', *,
            skip_children:bool = False, names_only:bool = True,
            options:ty.Optional[dict] = None) -> ty.Generator[DiffItem, None, None]:
	yield from FileListComparer(**(options or {})).compare(
		old_list, new_list,
		skip_children=skip_children, names_only=names_only)
