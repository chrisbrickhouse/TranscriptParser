"""
	Copyright (c) 2020 Christian Brickhouse

	This file is part of TranscriptParser

    TranscriptParser is free software: you can redistribute it
	and/or modify it under the terms of the GNU General Public License as
	published by the Free Software Foundation, either version 3 of the License,
	or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os

class Out():
	def __init__(self):
		self.output = ''

	def convert(
		self,
		transcript
	):
		codes = {}
		codeCounter = 0
		try:
			data = sorted(transcript.data,key=lambda x:float(x['start']))
		except TypeError:
			print(transcript.data)
			exit()
		outArray = []
		for row in data:
			speaker = row['speaker']
			if speaker not in codes:
				codes[speaker] = str(codeCounter)
				codeCounter += 1
			lineArray = [
				str(codes[speaker]),
				str(speaker),
				str(row['start']),
				str(row['end']),
				str(row['text'])
			]
			line = '\t'.join(lineArray)
			outArray.append(line)
		out = '\n'.join(outArray)
		self.output = out

	def save(self,fname,outDir='.'):
		fname = fname.split('.')[0]+'.txt'
		outPath = os.path.join(outDir,fname)
		with open(outPath,'w') as f:
			f.write(self.output)

	def clear(self):
		self.output=''
