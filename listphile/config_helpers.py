import enum
import functools
import typing as ty

if ty.TYPE_CHECKING:
	from . import paths

## Enums

_Enum = ty.TypeVar('Enum', bound=enum.Enum)

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

def _get_enum(enum_:ty.Type[_Enum], value:ty.Union[str,_Enum]) -> _Enum:
	if isinstance(value, enum_):
		return value
	if isinstance(value, str):
		try:
			return enum_[value.upper()]
		except KeyError:
			pass
	raise ValueError(f'Invalid {enum_.__name__} value: {value}')

def _enum_equals(value:ty.Union[str,_Enum], enum_value:_Enum):
	# value equals the enum or its string value
	return value == enum_value or (
	       isinstance(value, str) and value.upper() == enum_value.name)

## Sorting & grouping

_SortKey = ty.Callable[['paths.PathItem'], ty.Any]

_group_keys = {
	GroupType.MIXED: None,
	GroupType.FILESFIRST: lambda item: item.isdir, # files 0, dirs 1
	GroupType.FOLDERSFIRST: lambda item: not item.isdir # files 1, dirs 0
}

def join_keys(*keys:ty.Optional[_SortKey]) -> _SortKey:
	return lambda item: tuple(key(item) for key in keys if key)

def grouped_sort_key(sort_key:ty.Optional[_SortKey] = None,
                     item_grouping:ty.Union[GroupType,str] = GroupType.FILESFIRST
                     ) -> _SortKey:
	sort_key = sort_key or DEFAULTSORT
	item_grouping = _get_enum(GroupType, item_grouping)
	return join_keys(_group_keys[item_grouping], sort_key)

def group_sort_key(item_grouping:ty.Union[GroupType,str] = GroupType.FILESFIRST
	) -> ty.Callable[[_SortKey], _SortKey]:
	# decorator
	return functools.partial(grouped_sort_key, item_grouping=item_grouping)

DEFAULTSORT = lambda item: item.name
GROUPED_DEFAULTSORT = grouped_sort_key(DEFAULTSORT)
