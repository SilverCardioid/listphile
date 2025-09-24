import typing as ty
import eyed3

from .. import paths, format

def _data(item:paths.PathItem) -> ty.Optional[eyed3.core.AudioFile]:
	if 'audio' not in item._cache:
		item._cache['audio'] = eyed3.load(str(item.abspath)) if not item.isdir else None
	return item._cache['audio']

def _getYear(item:paths.PathItem):
	data = _data(item)
	if data and data.tag:
		date = data.tag.getBestDate()
		if date:
			return date.year or 0

def _add_props():
	format.Format._get_property.update({
		'duration'    : lambda item, options: int(_data(item).info.time_secs) if _data(item) and _data(item).tag else 0,
		'title'       : lambda item, options: _data(item).tag.title if _data(item) and _data(item).tag else '',
		'artist'      : lambda item, options: _data(item).tag.artist if _data(item) and _data(item).tag else '',
		'album'       : lambda item, options: _data(item).tag.album if _data(item) and _data(item).tag else '',
		'album_artist': lambda item, options: _data(item).tag.album_artist if _data(item) and _data(item).tag else '',
		'track_num'   : lambda item, options: _data(item).tag.track_num[0] if _data(item) and _data(item).tag else 0,
		'year'        : lambda item, options: _getYear(item)
	})
	format.Format._get_regex.update({
		'duration'    : lambda options: r'\d+?',
		'title'       : lambda options: r'.+?',
		'artist'      : lambda options: r'.+?',
		'album'       : lambda options: r'.+?',
		'album_artist': lambda options: r'.+?',
		'track_num'   : lambda options: r'\d+?',
		'year'        : lambda options: r'\d*?'
	})
