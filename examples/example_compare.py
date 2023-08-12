import os
import sys
sys.path.insert(1, os.path.abspath('..'))

import listphile

diffGen = listphile.compare('example_plain.txt', '..', skip_children=True)
for x in diffGen:
	print(x)