import os
import sys
sys.path.insert(1, os.path.abspath('..'))

import listphile

options = {
	'rel_to_cwd': True,
	'filter': lambda item: item.isdir and item.name in ('.git', '.idea', 'listphile.egg-info', '__pycache__')
}

# Plain format, default options
listphile.write_list('..', 'example_plain.txt', options)

# XML
options.update({
	'format_type': 'xml'
})
listphile.write_list('..', 'example_xml.xml', options)

# File data
options.update({
	'show_date': True,
	'show_size': True,
	'show_hash': True
})
listphile.write_list('..', 'example_data.xml', options)
