import typing as ty

import enum
import functools

## Enums

class FormatType(enum.Enum):
	PLAIN = 0
	XML = 1

class DateType(enum.Enum):
	NEWEST = 0
	CREATION = 1
	MODIFICATION = 2

class NameType(enum.Enum):
	DOT = 0
	NAME = 1
	RELPATH = 2
	ABSPATH = 3

class GroupType(enum.Enum):
	FILESFIRST = 0
	FOLDERSFIRST = 1
	MIXED = 2

def _enum_equals(value:ty.Union[str,enum.Enum], enum_value:enum.Enum):
	# value equals the enum or its string value
	return value == enum_value or (
	       isinstance(value, str) and value.upper() == enum_value.name)

## Sorting & grouping

_SortKey = ty.Callable[['paths.PathItem'], ty.Any]
def grouped_sort_key(sort_key:ty.Optional[_SortKey] = None,
                     item_grouping:ty.Union[GroupType,str] = GroupType.FILESFIRST
                     ) -> _SortKey:
	sort_key = sort_key or DEFAULTSORT
	if _enum_equals(item_grouping, GroupType.MIXED):
		# Sort by name (or other sort key) only
		return sort_key
	elif _enum_equals(item_grouping, GroupType.FILESFIRST):
		# Sort by (0,name) for files, (1,name) for dirs
		return lambda item: (item.isdir, sort_key(item))
	elif _enum_equals(item_grouping, GroupType.FOLDERSFIRST):
		# Sort by (1,name) for files, (0,name) for dirs
		return lambda item: (not item.isdir, sort_key(item))
	else:
		raise ValueError(f'unknown item_grouping value: {item_grouping}')

def group_sort_key(item_grouping:ty.Union[GroupType,str] = GroupType.FILESFIRST
	) -> ty.Callable[[_SortKey], _SortKey]:
	# decorator
	return functools.partial(grouped_sort_key, item_grouping=item_grouping)

DEFAULTSORT = lambda item: item.name
GROUPED_DEFAULTSORT = grouped_sort_key(DEFAULTSORT)
