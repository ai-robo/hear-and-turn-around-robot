import vosk, queue, json
import sounddevice as sd
import time
import threading
import doa
import serial

keyword_vars = ['привет робот', 'привет', 'робот', 'тест']
auto_define_dev_id = 1
records_count = 4
delay = 0.4 # Delay between records

def move_servo_to():
    results = []; i = 0
    while 1:
        results.append(doa.get_doa(device))
        i += 1
        if len(voice) == 0 or i >= records_count: break
        time.sleep(delay)
    dir = doa.calc_doa(results)
    print(f"Servo will moved to {dir}; directions recorded: {results}")
    port.write(bytes(str(dir),  'utf-8'))

q = queue.Queue()
devices = sd.query_devices()
port = serial.Serial(port='/dev/ttyACM0',  baudrate=115200, timeout=.1)

#while 1:
#    text = input()
#    port.write(bytes(str(text), 'utf-8'))

## Define device id
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


## Main code
try:
    #model = vosk.Model("path/to/vosk-model-ru")
    model = vosk.Model(lang="ru")
    device = doa.find_respeaker()
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=dev_id, dtype='int16', \
                            channels=1, callback=(lambda i, f, t, s: q.put(bytes(i)))):
        rec = vosk.KaldiRecognizer(model, samplerate)
        print("Ready. I'm listening...")

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                voice = json.loads(rec.Result())["text"]
                if len(voice) != 0:
                    if any(keyword in voice for keyword in keyword_vars):
                        move_servo = threading.Thread(target=move_servo_to)
                        move_servo.start()
                        time.sleep(1)

                        dir = doa.get_doa(device)
                        print(f"Recognized \"{voice}\" from {dir}")
                
except KeyboardInterrupt:
    print('\nDone')
