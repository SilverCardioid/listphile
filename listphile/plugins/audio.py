import eyed3

from .. import paths, format

def _data(item:paths.PathItem) -> eyed3.core.AudioFile:
	if item._cache.get('audio', None) is None:
		item._cache['audio'] = eyed3.load(str(item.abspath))
	return item._cache['audio']

def _add_props():
	format.Format._get_property.update({
		'duration'    : lambda item, options: int(_data(item).info.time_secs) if _data(item) else 0,
		'title'       : lambda item, options: _data(item).tag.title if _data(item) else '',
		'artist'      : lambda item, options: _data(item).tag.artist if _data(item) else '',
		'album'       : lambda item, options: _data(item).tag.album if _data(item) else '',
		'album_artist': lambda item, options: _data(item).tag.album_artist if _data(item) else '',
		'track_num'   : lambda item, options: _data(item).tag.track_num[0] if _data(item) else 0
	})
	format.Format._get_regex.update({
		'duration'    : lambda options: r'\d+?',
		'title'       : lambda options: r'.+?',
		'artist'      : lambda options: r'.+?',
		'album'       : lambda options: r'.+?',
		'album_artist': lambda options: r'.+?',
		'track_num'   : lambda options: r'\d+?'
	})
