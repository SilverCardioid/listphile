import os
from pathlib import Path
import typing as ty

from . import format, filelist, paths

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
		old_gen = _get_gen(old_list)
		new_gen = _get_gen(new_list)

		old_type, old_path, old_props = next(old_gen, (None, None, None))
		new_type, new_path, new_props = next(new_gen, (None, None, None))

		while old_type is not None or new_type is not None:
			diff = self._compare_lines(old_type, old_props, new_type, new_props)
			if diff == 0:
				assert old_path == new_path
				if (old_type == 'file' and not names_only and
				    self._compare_files(old_props, new_props)):
					yield DiffItem('change', new_type, new_path, old_props, new_props)
				else:
					yield DiffItem('match', new_type, new_path, old_props, new_props)
				old_type, old_path, old_props = next(old_gen, (None, None, None))
				new_type, new_path, new_props = next(new_gen, (None, None, None))

			elif diff < 0:
				yield DiffItem('deletion', old_type, old_path, old_props, None)

				can_skip_children = False
				if skip_children and new_type == 'dir':
					old_dir_depth = old_props.get_depth(self.options.start_level)
					if old_dir_depth is not None:
						can_skip_children = True
				old_type, old_path, old_props = next(old_gen, (None, None, None))
				while can_skip_children and old_props.get_depth(self.options.start_level) > old_dir_depth:
					old_type, old_path, old_props = next(old_gen, (None, None, None))

			else:
				yield DiffItem('addition', new_type, new_path, None, new_props)

				can_skip_children = False
				if skip_children and new_type == 'dir':
					new_dir_depth = new_props.get_depth(self.options.start_level)
					if new_dir_depth is not None:
						can_skip_children = True
				new_type, new_path, new_props = next(new_gen, (None, None, None))
				while can_skip_children and new_props.get_depth(self.options.start_level) > new_dir_depth:
					new_type, new_path, new_props = next(new_gen, (None, None, None))


	def _compare_lines(self, old_type:ty.Optional[str], old_props:format.Props,
	                         new_type:ty.Optional[str], new_props:format.Props):
		# positive result -> addition (old list ahead, new line missing in old list)
		# list that hasn't run out yet -> missing in other list
		if old_type is None or new_type is None:
			return (old_type is None) - (new_type is None)
		# higher indent -> missing in other list
		indent_diff = old_props.get_depth() - new_props.get_depth()
		if indent_diff != 0: 
			return -indent_diff
		# child file before child folder -> missing in other list
		isdir_diff = (old_type == 'dir') - (new_type == 'dir')
		if isdir_diff != 0:
			return isdir_diff
		# alphabetically first -> missing in other list
		else:
			old_name = old_props.get_name()
			new_name = new_props.get_name()
			return (old_name > new_name) - (old_name < new_name)


	def _compare_files(self, old_props:format.Props, new_props:format.Props):
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

def _get_gen(list_or_folder:paths.PathOrStr):
	if os.path.isdir(list_or_folder):
		return self.generate(list_or_folder)
	elif os.path.isfile(list_or_folder):
		return self.parse_list(list_or_folder)
	else:
		raise FileNotFoundError(list_or_folder)
