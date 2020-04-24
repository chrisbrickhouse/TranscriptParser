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
import re
import xml.etree.ElementTree as ET
from nltk.parse import CoreNLPParser

class TranscriptFile():
	annotations = re.compile(r"{.*?}")
	doubleParens = re.compile(r"\(\(.*?\)\)")
	incompleteWords = re.compile(r"\b(\w*?)-\s+\+(.+?)\b")
	def __init__(self, fname, type, inDir='.', outDir='.'):
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

	def initNlpParser(self, nlpURL='http://localhost:9000'):
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
