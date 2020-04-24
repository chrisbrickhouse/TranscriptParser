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
import argparse
import TranscriptParser.formats.Eaf as Eaf
import TranscriptParser.formats.Trs as Trs
import TranscriptParser.formats.FaveTsv as FaveTsv


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
	fave = FaveTsv.Out()
	for fname in transcriptFiles:
		if not os.path.isfile(os.path.join(inDir,fname)):
			print(f'Cannot find file: {fname}')
			continue
		print(fname)
		try:
			if '.eaf' in fname:
				transcript = Eaf.ElanTranscript(fname,inDir,outDir)
			elif '.trs' in fname:
				transcript = Trs.TranscriberTranscript(fname,inDir,outDir)
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
