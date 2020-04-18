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
	def __init__(self,fname, type):
		global inDir
		self.type = type
		self.fname = fname
		tree = ET.parse(os.path.join(inDir,fname))
		self.root = tree.getroot()
		self.textArray = []
		self.posTaggedArray = []
		self.nlpParserInit = False
		self.pos_tagger = None

	def getTranscript(self):
		return(self.textArray)

	def printTranscript(self,sep="\n"):
		print(sep.join(self.textArray))

	def initNlpParser(self):
		global nlpURL
		if not self.nlpParserInit:
			self.pos_tagger = CoreNLPParser(url=nlpURL, tagtype='pos')
			self.nlpParserInit = True

	def tag(self,line):
		if not self.nlpParserInit:
			self.initNlpParser()
		pos_tagged = list(self.pos_tagger.tag(line.split()))
		return(pos_tagged)

	def save(self,fname=None, type="transcript"):
		global outDir
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
	def __init__(self,fname):
		TranscriptFile.__init__(self,fname,'eaf')
		self.parse_eaf()

	def parse_eaf(self):
		counter = 0
		potentialSpeakerTiers = []
		for child in self.root:
			if child.tag == 'TIER':
				tierID = child.attrib['TIER_ID'].lower()
				if 'interviewer' in tierID or 'unknown' in tierID:
					continue
				else:
					potentialSpeakerTiers.append(child)
					counter += 1
		if counter == 0:
			raise ValueError('Cannot identify speaker tier')
		elif counter > 1:
			speakerTier = self._eafIdentifySpeaker(potentialSpeakerTiers)
		else:
			speakerTier = potentialSpeakerTiers[0]
		self._eafExtractTranscript(speakerTier)

	def _eafIdentifySpeaker(self,potentialSpeakerTiers):
		try:
			tiersNamedSpeaker = [x for x in potentialSpeakerTiers if 'speaker' in x.attrib['TIER_ID'].lower()]
		except Exception as e:
			print(potentialSpeakerTiers)
			exit(e)
		if len(tiersNamedSpeaker) == 1:
			return(tiersNamedSpeaker[0])
		elif len(tiersNamedSpeaker) == ( len( potentialSpeakerTiers ) - 1 ):
			return( [x for x in potentialSpeakerTiers if 'speaker' not in x.attrib['TIER_ID'].lower][0] )
		else:
			raise ValueError('Cannot identify speaker tier')

	def _eafExtractTranscript( self, speakerTier ):
		fullText = []
		posTaggedArray = []
		for text in speakerTier.itertext():
			text = self._clean_line(text)
			if text.strip() == '':
				continue
			fullText.append(text)
			try:
				posTaggedArray.append(self.tag(text))
			except Exception as e:
				print(repr(text))
				exit(e)
		self.textArray = fullText
		self.posTaggedArray = posTaggedArray

class TranscriberTranscriptFile(TranscriptFile):
	def __init__(self,fname):
		TranscriptFile.__init__(self,fname,'trs')
		self.speakerID = None
		self.parse_transcriber()


	def parse_transcriber(self):
		counter = 0
		potentialSpeakers = []
		for child in self.root:
			if child.tag == "Speakers":
				for speaker in child:
					name = speaker.attrib['name'].lower()
					if (
						'interviewer' in name or
						'other' in name or
						'unknown' in name or
						'unidentified' in name or
						'stranger' in name or
						'\\' in name
					):
						continue
					potentialSpeakers.append(speaker.attrib)
					counter += 1
				if counter == 0:
					raise ValueError('Cannot identify speaker ID')
				elif counter > 1:
					speakerID = self._trsIdentifySpeaker(potentialSpeakers)
				else:
					speakerID = potentialSpeakers[0]['id']
				self.speakerID = speakerID
			if child.tag == "Episode":
				self._trsExtractTranscript(child)

	def _trsIdentifySpeaker(self,potentialSpeakers):
		for speaker in potentialSpeakers:
			name = speaker['name'].split(' ')[::-1]
			if '_'.join(name) in self.fname:
				print('!!ACCEPT!!')
				return(speaker['id'])
		raise ValueError('Cannot identify speaker ID')

	def _trsExtractTranscript(self,contentTag):
		speakerID = self.speakerID
		fullText = []
		posTaggedArray = []
		for turn in contentTag.iter('Turn'):
			try:
				attribID = turn.attrib['id']
			except KeyError:
				try:
					attribID = turn.attrib['speaker']
				except KeyError:
					print('Turn with no ID')
					print(turn.attrib)
					continue
			if attribID != speakerID:
				continue
			for text in turn.itertext():
				text = self._clean_line(text)
				if text.strip() == '':
					continue
				fullText.append(text)
				posTaggedArray.append(self.tag(text))
		self.textArray = fullText
		self.posTaggedArray = posTaggedArray

def main(limit=0):
	global inDir
	global outType
	transcriptFiles = os.listdir(inDir)
	limitCounter = 0
	for fname in transcriptFiles:
		print(fname)
		try:
			if '.eaf' in fname:
				transcript = ElanTranscriptionFile(fname)
			elif '.trs' in fname:
				transcript = TranscriberTranscriptFile(fname)
			else:
				continue
		except ValueError as e:
			print(f'Could not parse {fname}')
			continue
		transcript.save(type=outType)
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
		"-g",
		"--tag",
		help="Run the part of speech tagger",
		action="store_true"
	)
	argparser.add_argument(
		"-x",
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
	args = argparser.parse_args()
	inDir = args.input
	outDir = args.output
	nlpURL = args.url+":"+args.port
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
