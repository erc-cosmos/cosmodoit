# Compute harmonic tension from a .musicXML (uncompressed) file
# uses Java applet XMLTensionVisualiser
import sys
import os
import argparse
import numpy as np
import pandas as pd
from subprocess import Popen, PIPE, call

def remove_extra_files(input_file):
	"""
	Check if TensionVisualiser generated excess files and remove them
	"""

	extra_files = [input_file + '_centroids.inscore',
				   input_file + '_diameter.inscore',
				   input_file + '_keydistance.inscore',
				   input_file + '_diameter.data',
				   input_file + '_centroid.data',
				   input_file + '_key.data',
				   input_file + '_tensionGraphs.html']
	for extra_file in extra_files:
		if os.path.isfile(extra_file):
			os.remove(extra_file)
			print('removed: ' + os.path.basename(extra_file))
	return

def get_fileType(input_file):
	"""
	get file extension
	"""

	file_tag = os.path.basename(input_file)
	[_, ext] = os.path.splitext(file_tag)
	return ext

def call_XmlTensionVisualiser(musicxml_file_in, meterUnits, windowLength):
	"""
	Use subprocess to execute XmlTension Visualiser from the command line on the input file
	input file: *.musicxml
	"""

	command_list = ['java', '-jar', 'XmlTensionVisualiser.jar',
					'-meterUnits', str(meterUnits),
					'-windowLength', str(windowLength),
					'-inputfile', musicxml_file_in]	
	process = Popen(command_list, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	print(stdout.decode('utf-8'))
	return

def call_AudioTensionVisualiser(txt_file_in, meterUnits, windowLength):
	"""
	Use subprocess to execute XmlTension Visualiser from the command line on the input file
	input file: *.txt
	"""

	# TODO: Account for discrepancies in naming between Audio and XML Visualisers
	command_list = ['java', '-jar', 'AudioTensionVisualiser.jar',
					# '-meterUnits', str(meterUnits),
					'-windowLength', str(windowLength),
					'-inputfile', txt_file_in]	
	process = Popen(command_list, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	print(stdout.decode('utf-8'))
	return

def compute_tension(input_file, meterUnits, windowLength):
	"""
	Get tension parameters from input file depending on extension
	"""

	ext = get_fileType(input_file)
	if ext == '.musicxml':
		call_XmlTensionVisualiser(input_file, meterUnits, windowLength)
	elif ext == '.txt':
		# call_AudioTensionVisualiser(input_file, meterUnits, windowLength)
		print('TO DO: correct name of .data files')
	return

def create_table(input_file):
	"""
	Read computed Tension files and create a csv
	"""

	diameter = np.loadtxt(input_file + '_diameter.data') # read files
	momentum = np.loadtxt(input_file + '_centroid.data')
	strain   = np.loadtxt(input_file + '_key.data')
	beat     = diameter[:, 0].astype(int)
	diameter = diameter[:, 1]
	momentum = np.insert(momentum[:, 1], 0, np.nan) # no value for first beat
	strain   = strain[:, 1]

	Tension  = pd.DataFrame.from_dict({'beat':beat,
									   'cloud_diameter':diameter,
									   'cloud_momentum':momentum,
									   'tensile_strain':strain})
	Tension.to_csv(os.path.splitext(input_file)[0] + '_Tension.csv', index=False) # export to csv
	return

def main(input_file, meterUnits=4, windowLength=8):
	"""
	Compute Harmonic Tension from input file using the TensionVisualiser Java tool
	 -input_file,--var <arg>   Input musicXML file.
	 -meterUnits,--var <arg>   option only used to change the inscore rendering:
	 						   number of units of meter. Default value is 4.
	 -windowLength,--var <arg> Length of the windows expressed as 4 (quarter note), 8, 16, etc.
							   Default value is eight note: 8.
	"""

	compute_tension(input_file, meterUnits, windowLength)
	create_table(input_file)
	remove_extra_files(input_file)
	return

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("input_file", type=str,
	                    help="Input musicXML or txt file")
	parser.add_argument("-m", "--meterUnits", type=int,
	                    help="Number of units of meter. Default value is 4")
	parser.add_argument("-w", "--windowLength", type=int, choices=[1, 2, 4, 8, 16, 32, 64],
	                    help="Length of the windows expressed as 4 (quarter), 8 (eight), etc.")
	args       = parser.parse_args()
	input_file = args.input_file
	if args.meterUnits:
		meterUnits = args.meterUnits
	else:
		meterUnits = 4
	if args.windowLength:
		windowLength = args.windowLength
	else:
		windowLength = 8

	main(input_file, meterUnits, windowLength)
	print('Done!')
