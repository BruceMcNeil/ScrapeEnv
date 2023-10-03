# -*- coding: utf-8 -*-

from pathlib import Path
from pathlib import PureWindowsPath
import shutil
import re
import pyttsx3
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment

class SpeakerError(Exception):
    def __init__(self, value):
            self.message = f"No such directory: {value}"
            super().__init__(self.message)

class Speaker(object):
    # properties
    #rootDirectory = 'H:\AUDIO-IN\\'
    # baseDirectory = rootDirectory + '\\PRODUCTS\\'
    inputDirectory = '\\INPUT\\'
    processedDirectory = inputDirectory + '\\PROCESSED\\'
    workDirectory = '\\TRANSFORM\\'
    outputDirectory = '\\OUTPUT\\'
    """
    pname = 'H:\AUDIO-IN\History of Roman Empire - Livy\\'
    aname = 'Wave\\'
    title = 'Volumes1-8.Gutenberg.txt'
    fname = pname + title
    afile = pname + aname + title
    finalFile = pname + title + '.wav'
    """

    # init
    def __init__(self, sourcePath, baseDirectory = 'D:\\PRODUCTS\\', inputDirectory = '\\INCOMING\\', processedDirectory = '\\PROCESSED\\', workDirectory = '\\TRANSFORM\\', outputDirectory='\\OUTPUT\\'):
        result = False
        self.baseDirectory = baseDirectory
        self.inputDirectory = inputDirectory
        self.processedDirectory = processedDirectory
        self.workDirectory = workDirectory
        self.outputDirectory = outputDirectory
        self.sourcePath = sourcePath
        self.sourceFileName = PureWindowsPath(self.sourcePath).name
        self.suffix = PureWindowsPath(self.sourcePath).suffix
        self.stem = PureWindowsPath(self.sourcePath).stem
        self.targetPath = self.baseDirectory + self.stem
        self.inputPath = self.targetPath + self.inputDirectory
        self.workPath = self.targetPath + self.workDirectory
        self.outputPath = self.targetPath + self.outputDirectory

        try:
            if (self.suffix != '.txt'):
                raise (SpeakerError(f'Need .txt file, not {self.sourcePath}'))
            if (Path(self.targetPath).exists() == False):
                Path(self.targetPath).mkdir()
            if (Path(self.targetPath).exists() and Path(self.targetPath).is_dir()):
                if (Path(self.inputPath).exists() == False):
                    Path(self.inputPath).mkdir()
                    if (Path(self.inputPath).exists() == False):
                        raise (SpeakerError(self.inputPath))
                if (Path(self.workPath).exists() == False):
                    Path(self.workPath).mkdir()
                    if (Path(self.workPath).exists() == False):
                        raise (SpeakerError(self.workPath))
                if (Path(self.outputPath).exists() == False):
                    Path(self.outputPath).mkdir()
                    if (Path(self.outputPath).exists() == False):
                        raise (SpeakerError(self.outputPath))
                shutil.copy(self.sourcePath, self.inputPath + self.sourceFileName)
                self.title = 'get this from targetPath leaf dir name'
            else:
                raise (SpeakerError(self.targetPath))
            # finish up init
        except Exception as e:
            print(f'Could not initialize Speaker class: problem path is {e}')
            result = False
        else:
            print(f'Successfully initialized Speaker class on path {self.targetPath}')
            self.pattern = re.compile(r"((\[)([0-9]*)(\]))")
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)
            self.voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', self.voices[1].id)
            self.txt = Path(self.sourcePath).read_text(encoding='utf-8')
            result = True


    # methods

    def say(self, text):
        self.engine.say(text)

    def processTxtToSpeech(self):
        result = False
        Lines = sent_tokenize(self.txt, language='english')
        count = 1
        productCount = 0
        sound1 = None
        combined_sounds = None
        for line in Lines:
            line = line.replace('\n\n', '. ')
            line = line.replace('\n', ' ')
            line = line.replace('  ', ' ')
            line = line.replace('  ', ' ')
            line = line.replace('  ', ' ')
            line = line.replace('  ', ' ')
            line = line.replace('  ', ' ')    
            line = line.replace('_ ',' "')
            line = line.replace(' _','" ')
            line = line.replace('Æ', 'Ae')
            line = line.replace('æ', 'ae')
            for match in self.pattern.finditer(line):
                line = line.replace(match.groups()[0], " -- Footnote number " + match.groups()[2] + " -- ")
            print (line)
            audioFile = self.workPath + 'temp.wav'
            count = count + 1
            self.engine.save_to_file(line, audioFile)
            self.engine.runAndWait()
            sound1 = AudioSegment.from_wav(audioFile)
            if (combined_sounds != None):
                combined_sounds = combined_sounds + sound1
            else:
                combined_sounds = sound1
            if (count > 1200):
                count = 0
                productCount = productCount + 1
                productFile = self.outputPath + self.stem + '.' + str(productCount) + '.mp3'
                combined_sounds.export(productFile, format="mp3")
                combined_sounds = None
        if (count > 0):
                count = 0
                productCount = productCount + 1
                productFile = self.outputPath + self.stem + '.' + str(productCount) + '.mp3'
                combined_sounds.export(productFile, format="mp3")
                combined_sounds = None
        print('\n\n\n\n\n')
        print('\n\n\n\nCOMPLETE!!!!')
        self.engine.stop()
        result = True
        return result

    # end Speaker class
"""

    main program

"""
if __name__ == "__main__":
    print(f'Load as module')