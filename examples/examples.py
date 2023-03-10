import os
import sys
sys.path.insert(1, os.path.abspath('..'))

import listphile

options = {'rel_to_cwd': True, 'filter_hidden':True}

# Plain format, default options
listphile.write_list('..', 'example_plain.txt', options)

# XML
options['format_type'] = 'xml'
listphile.write_list('..', 'example_xml.xml', options)
