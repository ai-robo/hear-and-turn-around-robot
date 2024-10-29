import vosk, queue, json
import sounddevice as sd

q = queue.Queue()

devices = sd.query_devices()
print("Select device id: \n", devices)
dev_id = 0 # default

try:
  dev_id = int(input())
except ValueError:
  print("Using default value: 0")

samplerate = int(sd.query_devices(dev_id, 'input')['default_samplerate'])

try:
  model = vosk.Model("/path/to/vosk-model-ru")
  with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=dev_id, dtype='int16', \
       channels=1, callback=(lambda i, f, t, s: q.put(bytes(i)))):
    rec = vosk.KaldiRecognizer(model, samplerate)

    while True:
      data = q.get()
      if rec.AcceptWaveform(data):
        data = json.loads(rec.Result())["text"]
        print("Recognized: " + data)
                
except KeyboardInterrupt:
    print('\nDone')
