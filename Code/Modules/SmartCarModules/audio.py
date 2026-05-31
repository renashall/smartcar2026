import pyaudio
import wave

chunk = 2**12

class audioPlayer:
    file_name = ''
    audio_file = None
    audio = pyaudio.PyAudio() 
    stream = None
    finished = True
    opened = False
    
    def __init__(self, song = None):
        if song:
            self.loadSong(song)
    
    def loadSong(self):
        if opened:
            self.closeSong()
            
        self.file_name = song
        self.audio_file = wave.open(file_name, 'rb')
        self.stream = self.audio.open(format = self.audio.get_format_from_width(self.audio_file.getsampwidth()),
                        channels=self.audio_file.getnchannels(),
                        rate=self.audio_file.getframerate(),
                        output=True)
        self.finished = False
        self.opened = True
        
    def playSong(self):
        print("Now playing", file_name)

        data = self.audio_file.readframes(chunk) #read from buffer

        while len(data) > 0: #while there is data to read
            self.stream.write(data)
            data = self.audio_file.readframes(chunk) #save frames
        
        self.closeSong()        
        
    def nextFrame(self):
        if self.finished:
            print(self.file_name, "Finished")
            return

        data = self.audio_file.readframes(chunk) #read from buffer
        
        if len(data) == 0:
            self.finished = True
        else:
            self.stream.write(data)
            
    def closeSong(self):
        if self.opened:
            self.stream.stop_stream()
            self.stream.close()
            self.audio_file.close()
            print(self.file_name, "has been closed")
            self.opened = False

        
