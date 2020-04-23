# Transcript Parser 0.2.0

Transcript parser is a python script to convert XML transcript files into human
readable, plain text transcripts along with optional Part of Speech tagging. It
currently supports the following file types.

### Supported File types
* .eaf (ELAN)
* .trs (Transcriber)

### Supported Output types
* .txt A plain text transcript
* .tsv Words are separated by tabs with the line above containing the associated
part of speech tag

## Quick Start
### (Optional) Stanford CoreNLP
#### Download
Install the nltk package for python using:
```bash
pip install nltk
```

Then in the directory where you want to store the CoreNLP files, run the following:
```bash
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-02-27.zip
unzip stanford-corenlp-full-2018-02-27.zip
cd stanford-corenlp-full-2018-02-27
```

#### Start the server
In the CoreNLP directory, start the server with:
```bash
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
-preload tokenize,ssplit,pos,lemma,ner,parse,depparse \
-status_port 9000 -port 9000 -timeout 15000 &
```

For information on these options see the [full CoreNLP documentation](https://stanfordnlp.github.io/CoreNLP/cmdline.html).

### Running the program
The simplest way to run the program is to download the python script and place
it in the directory containing the transcript files. Then run:
```bash
python TranscriptParser.py
```

To run the part of speech tagging, set the ```--tag``` flag:
```bash
python TranscriptParser.py --tag
```

You can specify input and output directories using command line arguments, allowing
you to run the program from any directory. For example:
```bash
python TranscriptParser.py -i transcribedFiles -o taggedFiles
```

You can get a full list of command line arguments from the help interface:
```bash
python TranscriptParser.py --help
```

## License
Your use of this program is licensed under the GNU General Public License v3 or
(at your option) any later version. You may use, modify, and distribute this
program and derivative works provided you attribute the original authors and
distribute your derived versions under the same license (among other terms
specified in the file COPYING)
