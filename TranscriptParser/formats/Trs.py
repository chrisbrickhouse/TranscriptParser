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

class TranscriberTranscript(Transcript.TranscriptFile):
	def __init__(self,fname,inDir='.',outDir='.'):
		super().__init__(fname,'trs',inDir,outDir)
		self.speakerID = None
		self.speakers = {
			'Unidentified Speaker':'Unidentified Speaker'
		}

	def parse(self):
		speakers = self.speakers
		data = []
		for child in self.root:
			if child.tag == "Speakers":
				for speaker in child:
					name = speaker.attrib['name']
					id_ = speaker.attrib['id']
					speakers[id_] = name
			elif child.tag == 'Episode':
				for turn in child.iter('Turn'):
					lines = self._parseTurn(turn)
					data = data + lines
		self.data = data

	def _parseTurn(self, turn):
		try:
			speakerList = turn.attrib['speaker'].split()
		except KeyError:
			# print('WARN: Turn has no speaker')
			speakerList = [None]
		data = []
		if len(speakerList) == 1:
			data = data + self._parseSingleSpeakerTurn(turn)
		elif len(speakerList) > 1:
			data = data + self._parseMultiSpeakerTurn(turn)
		else:
			raise ValueError('Turn has no speaker')
		return(data)

	def _parseSingleSpeakerTurn(self, turn):
		cache = []
		turnEnd = turn.attrib['endTime']
		syncIter = turn.iter()
		next(syncIter)
		for subelement in syncIter:
			tail = subelement.tail.strip()
			start = float(subelement.attrib['time'])
			try:
				speakerID = turn.attrib['speaker']
			except KeyError:
				speakerID = 'Unidentified Speaker'
			struct = {
				'speaker': self.speakers[speakerID],
				'start': start,
				'end': None,
				'text': tail
			}
			cache.append(struct)
		cache[-1]['end'] = float(turnEnd)
		for i in range(len(cache)-1):
			cache[i]['end'] = float(cache[i+1]['start'])
		return(cache)

	def _parseMultiSpeakerTurn(self, turn):
		cache = {}
		out = []
		syncPoint = 0.0
		turnEnd = float(turn.attrib['endTime'])
		for i in range(len(list(turn))):
			subelement = turn[i]
			tail = subelement.tail.strip()
			if subelement.tag == 'Sync':
				syncPoint = subelement.attrib['time']
			elif subelement.tag == 'Who':
				code = 'spk'+subelement.attrib['nb']
				struct = {
					'speaker': self.speakers[code],
					'start': float(syncPoint),
					'end': turnEnd if i == len(list(turn)) else None,
					'text': tail
				}
				if code not in cache:
					cache[code] = []
				cache[code].append(struct)
		for k,v in cache.items():
			for i in range(len(v)-1):
				v[i]['end'] = v[i+1]['start']
			out = out + v
		return(out)
