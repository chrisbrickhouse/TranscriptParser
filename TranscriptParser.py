"""
	Copyright (c) 2020 Christian Brickhouse

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import re
import argparse
import xml.etree.ElementTree as ET
from nltk.parse import CoreNLPParser

class TranscriptFile():
	annotations = re.compile(r"{.*?}")
	doubleParens = re.compile(r"\(\(.*?\)\)")
	incompleteWords = re.compile(r"\b(\w*?)-\s+\+(.+?)\b")
	def __init__(self,fname, type, inDir='.', outDir='.'):
		self.type = type
		self.fname = fname
		tree = ET.parse(os.path.join(inDir,fname))
		self.root = tree.getroot()
		self.textArray = []
		self.posTaggedArray = []
		self.nlpParserInit = False
		self.pos_tagger = None
		self.data = []
		self.outDir = outDir

	def getTranscript(self):
		return(self.textArray)

	def printTranscript(self,sep="\n"):
		print(sep.join(self.textArray))

	def initNlpParser(self):
		global nlpURL
		if not self.nlpParserInit:
			self.pos_tagger = CoreNLPParser(url=nlpURL, tagtype='pos')
			self.nlpParserInit = True

	def tag(self):
		data = self.data
		if data == []:
			raise ValueError('Transcript data is empty. Have you parsed it?')
		if not self.nlpParserInit:
			self.initNlpParser()

		fullText = []
		posTaggedArray = []
		for struct in data:
			line = struct['text'].strip()
			text = self._clean_line(line)
			if text.strip() == '':
				continue
			tagged = self.pos_tagger.tag(text.split())
			posTaggedArray.append(list(tagged))
		self.posTaggedArray = posTaggedArray

	def save(self,fname=None, type="transcript"):
		outDir = self.outDir
		if type == "pos tagged":
			ext = '.tsv'
			tagged = self.posTaggedArray
			outArray = []
			for line in tagged:
				top = '\t'.join([x[1] for x in line])
				bottom = '\t'.join([x[0] for x in line])
				outArray.append(top+'\n'+bottom)
			outText = '\n'.join(outArray)
		else:
			ext = '.txt'
			outText = '\n'.join(self.textArray)
		if not fname:
			fname = self.fname.split('.')[0]+ext
		outFile = os.path.join(outDir,fname)
		with open(outFile,'w') as f:
			f.write(outText)

	def _clean_line(self,text):
		text = text.strip()
		text.replace('*','')
		text = re.sub(
			self.annotations,
			'',
			text
		)
		text = re.sub(
			self.doubleParens,
			'',
			text
		)
		text = re.sub(
			self.incompleteWords,
			r"\2",
			text
		)
		return(text)


class ElanTranscriptionFile(TranscriptFile):
	def __init__(self,fname,inDir='.',outDir='.'):
		TranscriptFile.__init__(self,fname,'eaf',inDir,outDir)
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


class TranscriberTranscriptFile(TranscriptFile):
	def __init__(self,fname,inDir='.',outDir='.'):
		TranscriptFile.__init__(self,fname,'trs',inDir,outDir)
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


class FaveTsv():
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

	def save(self,fname):
		global outDir
		fname = fname.split('.')[0]+'.txt'
		outPath = os.path.join(outDir,fname)
		with open(outPath,'w') as f:
			f.write(self.output)

	def clear(self):
		self.output=''


def main(limit=0):
	global inDir
	global outType
	global listPath
	if listPath:
		with open(listPath) as f:
			transcriptFiles = [x.strip() for x in f.readlines()]
	else:
		transcriptFiles = os.listdir(inDir)
	limitCounter = 0
	fave = FaveTsv()
	for fname in transcriptFiles:
		if not os.path.isfile(os.path.join(inDir,fname)):
			print(f'Cannot find file: {fname}')
			continue
		print(fname)
		try:
			if '.eaf' in fname:
				transcript = ElanTranscriptionFile(fname,inDir,outDir)
			elif '.trs' in fname:
				transcript = TranscriberTranscriptFile(fname,inDir,outDir)
			else:
				continue
		except ValueError as e:
			print(f'Could not parse {fname}')
			continue
		transcript.parse()
		if outType == 'pos tagged':
			transcript.tag()
			transcript.save(type=outType)
		else:
			fave.convert(transcript)
			fave.save(fname)
			fave.clear()
		del transcript
		limitCounter += 1
		if limit > 0 and limitCounter >= limit:
			break

if __name__ == "__main__":
	argparser = argparse.ArgumentParser()
	argparser.add_argument(
		"-i",
		"--input",
		help="Path to input directory containing transcription files.",
		default="."
	)
	argparser.add_argument(
		"-o",
		"--output",
		help="Path to output directory.",
		default="."
	)
	argparser.add_argument(
		"-l",
		"--limit",
		help="Number of files to process",
		type=int,
		default=0
	)
	argparser.add_argument(
		"--tag",
		help="Run the part of speech tagger",
		action="store_true"
	)
	argparser.add_argument(
		"--text",
		help="Plain text output",
		action="store_true"
	)
	argparser.add_argument(
		"-u",
		"--url",
		help="URL for the CoreNLP server",
		default="http://localhost"
	)
	argparser.add_argument(
		"-p",
		"--port",
		help="Port to access the CoreNLP server",
		type=str,
		default="9000"
	)
	argparser.add_argument(
		"--list",
		help="Path to a file containing a list of items to parse."
	)
	args = argparser.parse_args()
	inDir = args.input
	outDir = args.output
	nlpURL = args.url+":"+args.port
	listPath = None
	if args.list:
		if not os.path.isfile(args.list):
			raise FileNotFoundError()
		else:
			listPath = args.list
	if not os.path.isdir(inDir):
		raise NotADirectoryError(inDir)
	if not os.path.isdir(outDir):
		raise NotADirectoryError(outDir)
	if args.tag and args.text:
		raise Exception()
	elif args.tag:
		outType = "pos tagged"
	else:
		outType = "transcript"
	main(args.limit)
