#!/opt/anaconda3/bin/python python3
# -*- coding: utf-8 -*-
import sys
import os
import re

def regex_search(pattern, file_name):
	"""
	For each line of the input text file, find all occurrences of a pattern
	using regular expressions and return a list.
	Doesn't return lines where there are no matches
	"""
	remove_arr = []
	res = []
	remain_line = []
	for line in file_name:
		j = re.findall(pattern, line)
		if len(j) !=0:
			stringList = ' '.join([str(item[0]) for item in j ])
			res.append(stringList)
	return res

def rename_cleaned(text_file_in, new_tag='_cleaned', new_ext=''):
	"""
	Add the tag '_cleaned' to the file name given by antescofo
	"""
	file_tag = os.path.basename(text_file_in)
	[fname, ext] = os.path.splitext(file_tag)
	if new_ext=='':
		text_file_out = os.path.join(os.path.dirname(text_file_in), fname + new_tag + ext)
	else:
		text_file_out = os.path.join(os.path.dirname(text_file_in), fname + new_tag + new_ext)
	return text_file_out

def call_antescofo(antescofo_path, musicxml_path, tracks=1):
	"""
	Use subprocess to execute antescofo importer from the command line on the input file
	"""
	from subprocess import Popen, PIPE, call
	import os
	
	tracks             = '-tracks='+str(tracks)
	antescofo_fullpath = os.path.join(antescofo_path, 'antescofo_importer')
	call(['chmod', 'u+x', antescofo_fullpath])    # change persmission to execute
	process = Popen([antescofo_fullpath,
					tracks, '-originalpitches',
					musicxml_path], stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	print(stdout.decode('utf-8'))

def main(text_file_in, regex_pattern, rename=True):
	"""
	Parse text file from antescofo and output only useful notes
	text_file_in  : text file from antescofo importer
	regex_pattern : regular expression pattern to match and search
	"""
	if rename:
		text_file_out = rename_cleaned(text_file_in)
	else:
		text_file_out = text_file_in

	with open(text_file_in, 'r') as txtfile:
		data = txtfile.read()
	data = data.split('\n')
	main_data = data
	regl = []

	# Search and return matches
	regexp_results = regex_search(regex_pattern, main_data)

	# Write to txt file 
	with open(text_file_out, 'w') as fp:
		fp.write('\n'.join('{}'.format(x) for x in regexp_results))

if __name__ == '__main__':
	# TO DO: use argparse to handle input arguments (optional antescofo path, track) and help
	musicxml_file_in = str(sys.argv[1])
	# Call antescofo importer
	antescofo_path = os.path.dirname(os.path.realpath(__file__)) # Assuming antescofo_importer is in the current directory
	track          = 1                                           # Assuming that we're interested in the 1st track
	call_antescofo(antescofo_path, musicxml_file_in, track)
	# Get filename with antescofo output syntax
	text_file_in  = rename_cleaned(musicxml_file_in, new_tag='.asco', new_ext='.txt')
	regex_pattern = r'([CDEFGAB](#|b)?[\d])'
	# Remove all non-note elements (first pass)
	main(text_file_in, regex_pattern)
	regex_pattern = r'([CDEFGAB](#|b)?)'
	text_file_in  = rename_cleaned(text_file_in)
	# Remove note numbers (second pass)
	main(text_file_in, regex_pattern, False)
	print('Done!')
