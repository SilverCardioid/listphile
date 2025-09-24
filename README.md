# listphile

A Python library for making lists of files (get it?) using a customisable format.

Given one or more base folders, it recursively traverses descendant folders and files depth-first, and lists them with any specified file data. It can also parse and compare lists.

## Installation
```
pip install git+https://github.com/SilverCardioid/listphile.git
```

To include optional dependencies for audio metadata support:
```
pip install git+https://github.com/SilverCardioid/listphile.git[audio]
```


## Usage example

### Command line
```
# Print a file list to the screen
python -m listphile list path/to/folder
# Save it to a file
python -m listphile list path/to/folder -o output_file.txt
```
Use `python -m listphile list -h` to see the list of arguments.

### Library
```python
import listphile
listphile.write_list('path/to/folder', 'output_file.txt')
```

Output list for this repository using the default format:
```
<.>
 .gitignore
 README.md
 pyproject.toml
 <examples>
  example_compare.py
  example_data.xml
  example_plain.txt
  example_xml.xml
  examples.py
 <listphile>
  __init__.py
  __main__.py
  command_line.py
  compare.py
  config.py
  config_helpers.py
  filelist.py
  format.py
  paths.py
  <plugins>
   audio.py
```

Or, using an XML format by setting the `format_type` [option](#options):
```xml
<Folder>
 <File name=".gitignore"/>
 <File name="README.md"/>
 <File name="pyproject.toml"/>
 <Folder name="examples">
  <File name="example_compare.py"/>
  <File name="example_data.xml"/>
  <File name="example_plain.txt"/>
  <File name="example_xml.xml"/>
  <File name="examples.py"/>
 </Folder>
 <Folder name="listphile">
  <File name="__init__.py"/>
  <File name="__main__.py"/>
  <File name="command_line.py"/>
  <File name="compare.py"/>
  <File name="config.py"/>
  <File name="config_helpers.py"/>
  <File name="filelist.py"/>
  <File name="format.py"/>
  <File name="paths.py"/>
  <Folder name="plugins">
   <File name="audio.py"/>
  </Folder>
 </Folder>
</Folder>
```

See the [examples](/examples) folder for a few more examples.

## Reference

### Main functions

#### write_list
```python
listphile.write_list(folder:str|Path|Sequence[str|Path] = '',
                     list_path:str|Path|TextIO = '',
                     options:dict|None = None)
```
Make a file list and save it to a file. Equivalent to `listphile.FileLister(**options).write_list(folder, list_path)`.

`folder` is the path to the list's base folder(s), and can be a string, [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html), or a sequence of either. The empty string, `'.'` or `None` represents the current working directory.

See [below](#options) for the possible options.

#### generate
```python
listphile.generate(folder:str|Path|Sequence[str|Path] = '',
                   options:dict|None = None) -> Generator[ListItem]
```
A generator function yielding `ListItem`s for descendant files and folders, recursively. Equivalent to `listphile.FileLister(**options).generate(folder)`.

`ListItem` is a [NamedTuple](https://docs.python.org/3/library/typing.html#typing.NamedTuple) containing three fields:
* `item_type` (`str`): the [item type](#formats-properties) (`file`, `dir`, `dir_close` or `ellipsis`).
* `path` ([`pathlib.Path`](https://docs.python.org/3/library/pathlib.html)): the path relative to the base folder.
* `props` ([`Props`](#helper-classes)): the file or folder properties.

The included item types depend on the options; only types with non-empty formats will be yielded.

#### parse_list
```python
listphile.parse_list(list_path:str|Path|TextIO,
                     options:dict|None = None) -> Generator[ListItem]
```
Parse a file list that was created using the given format options line-by-line, and yield files and folders similarly to `generate()`. Equivalent to `listphile.FileLister(**options).parse_list(list_path)`.

This requires newline-separated items, and does not yet support files with headers or footers. A warning is printed if a line doesn't match a format string or matches multiple format types.

#### compare
```python
listphile.compare(old_list:str|Path|TextIO,
                  new_list:str|Path|TextIO = '.', *,
                  skip_children:bool = False,
                  names_only:bool = True,
                  options:dict|None = None) -> Generator[DiffItem]
```
A generator function that matches items from the two source lists based on their folder structures, filenames and optionally properties. Equivalent to `listphile.FileListComparer(**options).compare(old_list, new_list, skip_children=skip_children, names_only=names_only)`.

It yields `DiffItem`s, a [NamedTuple](https://docs.python.org/3/library/typing.html#typing.NamedTuple) containing the following fields:
* `diff_type` (`str`): one of four strings:
    * `addition` if the item only appears in the new list;
    * `deletion` if the item only appears in the old list;
    * `match` if the item appears in both lists;
    * `change` if the item appears in both lists but their properties differ (only for files, and only if `names_only` is False).
* `item_type` (`str`): the [item type](#formats-properties) (`file`, `dir`, `dir_close` or `ellipsis`).
* `path` ([`pathlib.Path`](https://docs.python.org/3/library/pathlib.html)): the file path relative to the base folder.
* `old_props` ([`Props`](#helper-classes)): the properties for the old list item, or `None` for additions.
* `new_props` (`Props`): the properties for the new list item, or `None` for deletions.

Both source lists can be a file path or object, which will be read and parsed as a file list (see [`parse_list()`](#parse_list)), or a path to a folder to traverse the contents of.

If `skip_children` is True, the contents of folders that only appear in one list will be omitted, instead of their whole subtree being included as additions or deletions. If `names_only` is False, also compare the available file properties (hash, file size and dates) for determining the `diff_type`.

### Classes

#### FileLister
```python
fl = listphile.FileLister(**options)
```
The main class; it stores a set of formats and other options, and provides methods to write, read or generate filelists according to those options. See [below](#options) for the possible options.

Methods:
* `set_formats(*, file_format:str|None = None, dir_format:str|None = None, dir_close_format:str|None = None, root_format:str|None = None, ellipsis_format:str|None = None)`<br/>Set or reset the five [formats](#formats-properties). Each of them is replaced by the given value, or if that is None, recalculated from the [list options](#options).
* `write_list(folder:str|Path|Sequence[str|Path] = '', list_path:str|Path|TextIO = '')`<br/>Write a file list to a file; see [write_list](#write_list).
* `generate(folder:str|Path|Sequence[str|Path] = '') -> Generator[ListItem]`<br/>Recursively yield files and folders; see [generate](#generate).
* `parse_list(list_path:str|Path|TextIO) -> Generator[ListItem]`<br/>Read a file list from a file; see [parse_list](#parse_list).
* `run_folder(folder:str|Path = '', *, args:dict|None = None)`<br/>Traverse a single base folder and call the methods below for each file or folder, passing through a [`PathItem`](#helper-classes) and the provided `args`. By default, these methods write formatted list items to the file-like object stored in `args['file']` (this is used internally for `write_list()`). The behaviour can be customised by subclassing `FileLister` and overriding the four item methods:
    * `dir_function(self, item:PathItem, args:dict|None = None)`
    * `file_function(self, item:PathItem, args:dict|None = None)`
    * `ellipsis_function(self, item:PathItem, args:dict|None = None)`
    * `dir_close_function(self, item:PathItem, args:dict|None = None)`

#### FileListComparer
```python
flc = listphile.compare.FileListComparer(**options)
```
A subclass of `FileLister` that adds functionality to compare lists. It has one additional method:
* `compare(old_list:str|Path|TextIO, new_list:str|Path|TextIO = '.', *, skip_children:bool = False, names_only:bool = True) -> Generator[DiffItem]`<br/>Compare two filelists; see [compare](#compare).

#### Helper classes
**`FormatType`, `NameType`, `GroupType`**: Various enum classes used in [list options](#options). Each of the relevant options also accepts a case-insensitive string instead of an actual enum value (e.g. `'plain'` instead of `FormatType.PLAIN`).

**`PathItem`**: A class representing a folder or file, used as a parameter in callback functions. It has the following properties and methods:
* `name` (`str`)<br/>File/folder name.
* `path` (`pathlib.Path`)<br/>Relative path.
* `abspath` (`pathlib.Path`)</br>Absolute path.
* `depth` (`int`)<br/>Tree depth relative to the base folder.
* `isdir` (`bool`)<br/>`True` if the item is a directory.
* `hidden` (`bool`)<br/>`True` if the item is a hidden file or folder.
* `data` ([`os.stat_result`](https://docs.python.org/3/library/os.html#os.stat_result))<br/>Item metadata as returned by [`os.stat()`](https://docs.python.org/3/library/os.html#os.stat), cached on the first call.
* `hash(*, buffer_size:int = 1048576, max_size:int|None = None) -> str`<br/>Read through the file in chunks of size `buffer_size`, and calculate its [SHA-1](https://en.wikipedia.org/wiki/SHA-1) hash. Returns the empty string if the item is not a file, or if the file size exceeds the given `max_size`.
* `get_name(name_type:NameType|str = NameType.NAME) -> str`<br/>Get the item name or path according to the given `NameType` setting.
* `iterdir() -> Generator[PathItem]`<br/>Generate the folder's child items in arbitrary order using [`Path.iterdir()`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.iterdir).
* `children(key:Callable[[PathItem],Any]|None = None) -> list[PathItem]`<br/>List the folder's child items, sorted by the given `key` function. By default, sort according to the filename, with files appearing before folders.

**`Props`**: A `dict` subclass representing a set of item properties, returned by some generator functions. It adds the following methods for getting certain item data based on the available properties (returning `None` if there is not enough information):
* `get_depth(start_level:int = 0, *, indent:str = ' ') -> int|None`<br/>Get the zero-based depth. The parameters should match the corresponding file list options, and are used for calculating the depth from the indentation level.
* `get_name() -> str|None`<br/>Get the file/folder name.
* `get_path(item_type:str|None = None, parents:List[str]|None = None, *, depth:int|None = None, start_level:int = 0, indent:str = ' ') -> str|None`<br/>Get the item's relative path. `parents` is a list of ancestor folder names, which can simply be a reference to an initially empty list. The method automatically populates this list based on item depths and folder names, so that it contains the full directory path at any point during normal iteration. `start_level` and `indent` are passed through to `get_depth()`; the provided `depth` argument is used instead if that method is inconclusive.

### Formats & properties
The five main format types are:
* `file`: For normal files.
* `dir`: For folders/directories, printed before the folder's contents.
* `dir_close`: For folders/directories, printed after the folder's contents. Excluded by default in the plain layout, and used for the closing tag in the XML layout.
* `root`: For the root directory. Normally the same as dir_format, except a literal "." is printed instead of the folder name by default. Uses the item type `dir`.
* `ellipsis`: For marking the omission of folder contents due to `max_depth` being exceeded. Not printed by default. The properties are those of the folder.

Formats use standard [format strings](https://docs.python.org/3/library/stdtypes.html#str.format), which represent item properties by expressions in braces (e.g. `{name}`). The property values are filled in during list formatting, and are also returned by [generator functions](#main-functions) as a [`Props`](#helper-classes) dictionary. The following properties are supported:
* 'name': File/folder name.
* 'depth': Tree depth relative to the base folder.
* 'level': Indentation level (the depth offset by the `start_level` option).
* 'indent': Indentation string (the string specified by the `indent` option, repeated `level` times).
* 'relpath': Path relative to the base folder.
* 'abspath': Absolute path.
* 'hidden': The string specified by the `hidden` option if the file is hidden, otherwise the empty string.
* 'size': File size in bytes.
* 'cdate': Creation date (formatted according to the `date_format` option).
* 'mdate': Modification date (formatted according to the `date_format` option).
* 'ndate': Newest of creation and modification date.
* 'hash': SHA-1 hash.

The `audio` plugin (see [installation](#installation)) adds the following properties:
* 'duration': Track duration in seconds.
* 'title': Track title.
* 'artist': Track artist.
* 'album': Track album.
* 'album_artist': Track album artist.
* 'track_num': Track number.
* 'year': Track year.

#### add_property
Custom properties can be added statically using the top-level `add_property` function:

```python
listphile.add_property(key:str,
                       getter:Callable[[PathItem,Options],Any]|Any = '',
                       regex:Callable[[Options],str]|str = '.*?')
```
The `getter` is used to return the desired property value for each item. It can be a function taking a [`PathItem`](#helper-classes) and the current list's [`Options`](#options) with any return type, or a dummy constant value (by default, the empty string).

`regex` is a [regular expression](https://docs.python.org/3/library/re.html#regular-expression-syntax) pattern string used to parse the value from a string item in [`parse_list()`](#parse_list), and defaults to matching any string. It can also be a function that takes the current `Options` and returns a pattern string. Note that capturing groups in the pattern can mess up the property matching, so any parenthesised expressions should use the non-capturing syntax `(?:  )`.

Both functions are also passed the current list's [`Options`](#options).


### Options
These are the allowed options for the [`FileLister`](#filelister) and shorthand functions, with supported types and default values. They are passed into them as a `dict` and stored as attributes of an `Options` object, which is also accessible as the `options` property on an existing `FileLister`. Use the lister's `set_formats()` method to update the formats after changing option values.

Main format strings (if None, they will be automatically constructed based on the other options; if the empty string, nothing will be printed):
* `file_format: str|None = None`
* `dir_format: str|None = None`
* `dir_close_format: str|None = None`
* `root_format: str|None = None`
* `ellipsis_format: str|None = None`

File output options:
* `rel_to_cwd: bool = False`<br/>If `True`, resolve relative paths for output files with respect to to the current working directory; otherwise, resolve them with respect to the (first) base folder of the list itself.
* `append: bool = False`<br/>If `True`, append the list to the specified file instead of overwriting its contents.
* `header: str = ''`<br/>Text to be printed before the file list in the output file.
* `footer: str = ''`<br/>Text to be printed after the file list in the output file.

General format options:
* `format_type: FormatType|str = FormatType.PLAIN`<br/>Format family to use: `PLAIN` or `XML`.
* `show_indent: bool = True`<br/>Whether or not to indent lines.
* `indent: str = ' '`<br/>String used for each indentation level.
* `start_level: int = 0`<br/>Indentation level for the root folder.
* `max_depth: int|None = 20`<br/>Maximum depth for folder traversal (not counting the `start_level`). 0 or None for unlimited depth.
* `show_ellipsis: bool = False`<br/>Include or exclude ellipsis lines that indicate `max_depth` being exceeded.
* `ellipsis: str = '...'`<br/>String used for ellipsis lines in the plain layout.
* `newline: str = '\n'`<br/>String printed between lines.

Sorting and filtering:
* `show_folders: bool = True`<br/>Include or exclude folders.
* `show_files: bool = True`<br/>Include or exclude files.
* `filter: Callable[[PathItem],bool]|None = None`<br/>Filter function to exclude certain files or folders. Should take a [`PathItem`](#helper-classes) and return a `bool`; if it returns `True`, the item will be omitted from the list.
* `filter_hidden: bool = False`<br/>If `True`, exclude hidden files.
* `item_grouping: GroupType|str = GroupType.FILESFIRST`<br/>Specify whether or not child files are displayed before or after child folders in a directory: `FILESFIRST`, `FOLDERSFIRST` or `MIXED`.
* `sort_key: Callable[[PathItem],Any]|None = None`<br/>Function used for sorting. Should take a `PathItem` and return an object to be used as the sort key.

Item properties:
* `name_type: NameType|str = NameType.NAME`<br/>How to display item names: `NAME` (the file or folder name), `RELPATH` (the path relative to the root folder), or `ABSPATH`.
* `root_name_type: NameType|str = NameType.DOT`<br/>How to display the root folder: `DOT` (a literal ".") or any of the values for `name_type`.
* `show_size: bool = False`<br/>Display file sizes.
* `show_date: bool = False`<br/>Display file dates.
* `date_type: DateType|str = DateType.NEWEST`<br/>The type of date to display: `CREATION`, `MODIFICATION` or `NEWEST` (the later of the creation and modification dates).
* `date_format: str = '%Y%m%d%H%M%S'`<br/>A date format supported by [datetime.strftime](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).
* `show_hash: bool = False`<br/>Display the [SHA-1](https://en.wikipedia.org/wiki/SHA-1) hash for files.
* `show_hidden: bool = False`<br/>Mark hidden files.
* `hidden: str = '*'`<br/>String used for marking hidden files.
* `properties: Iterable[str]|None = None`<br/>Additional [properties](#formats--properties) to include in the output of [`generate()`](#generate) beyond those in the format strings.
