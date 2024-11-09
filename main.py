import vosk, queue, json
import sounddevice as sd
import doa

#keyword = "робот"
auto_define_dev_id = 1

q = queue.Queue()
devices = sd.query_devices()

if auto_define_dev_id:
    for id in str(devices).split("\n"):
        if "ReSpeaker 4 Mic Array" in id:
            dev_id = int(id.split()[0])
            break
else:
    print("Select device id: \n", devices)
    dev_id = 0 # default

    try:
        dev_id = int(input())
    except ValueError:
        print("Using default value: 0")

samplerate = int(sd.query_devices(dev_id, 'input')['default_samplerate'])

try:
    model = vosk.Model(lang="ru")
    device = doa.find_respeaker()
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=dev_id, dtype='int16', \
                            channels=1, callback=(lambda i, f, t, s: q.put(bytes(i)))):
        rec = vosk.KaldiRecognizer(model, samplerate)

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                voice = json.loads(rec.Result())["text"]
                #if rec.AcceptWaveform(data):
                if len(voice) != 0:
                #if keyword in voice:
                    result = doa.get_doa(device)
                    print(f"Recognized \"{voice}\" from {result}")
                
except KeyboardInterrupt:
    print('\nDone')
