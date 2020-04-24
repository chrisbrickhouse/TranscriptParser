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
from . import Transcript

class ElanTranscript(Transcript.TranscriptFile):
	def __init__(self,fname,inDir='.',outDir='.'):
		super().__init__(fname, 'eaf', inDir, outDir)
		self.timeOrders = []

	def _parseTimeOrders(self):
		timeOrderTag = None
		orders = []
		for child in self.root:
			if child.tag == 'TIME_ORDER':
				for slot in child:
					try:
						orders.append(slot.attrib['TIME_VALUE'])
					except KeyError:
						print('Potential error in',self.fname)
						orders.append(0)
				break
		self.timeOrders = orders

	def _tsIndex(self, slot):
		return(int(slot.split('s')[1])-1)

	def parse(self):
		data = []
		self._parseTimeOrders()
		timeOrders = self.timeOrders
		for child in self.root:
			if child.tag == 'TIER':
				name = child.attrib['TIER_ID']
				for element in child.iter('ALIGNABLE_ANNOTATION'):
					startRef = self._tsIndex(element.attrib['TIME_SLOT_REF1'])
					endRef = self._tsIndex(element.attrib['TIME_SLOT_REF2'])
					start = int(timeOrders[startRef])/1000.0  # convert ms to seconds
					end = int(timeOrders[endRef])/1000.0  # convert ms to seconds
					text = element.find('ANNOTATION_VALUE').text
					if text == None:
						continue
					text = self._clean_line(text)
					if text.strip() == '':
						continue
					line = {
						'speaker': name,
						'start': start,
						'end': end,
						'text': text
					}
					data.append(line)
		self.data = sorted(data,key=lambda x:float(x['start']))

	def text(self,speakerIDs=None):
		if speakerIDs:
			if type(speakerIDs) == list:
				raise NotImplementedError() # Need to move code determination to self.parse() from FaveTsv
			elif type(speakerIDs) == str:
				raise NotImplementedError()
			else:
				raise TypeError('IDs must be a string or list of strings')
		else:
			return('\n'.join([x['text'] for x in self.data]))
