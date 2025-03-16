import vosk, queue, json
import sounddevice as sd
import time
import threading
import doa
import cv2
import os
import serial
import pyaudio
from speechkit import Session, SpeechSynthesis
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage

gigachat_creds = os.environ.get("GIGACHAT_CREDS")
oauth_token = os.environ.get("OAUTH_TOKEN")
catalog_id = os.environ.get("CATALOG_ID")


keyword_vars = ['привет робот', 'привет', 'робот', 'тест']
keyword_vars2 = ['опиши, что ты видишь', 'что ты видишь', 'видишь', 'опиши']

auto_define_dev_id = True
records_count = 4
delay = 0.4 # Delay between records
serial_port = '/dev/ttyUSB0'

# ============================ servo ==========================

def move_servo_to():
    results = []; i = 0
    while 1:
        results.append(doa.get_doa(device))
        i += 1
        if len(voice) == 0 or i >= records_count: break
        time.sleep(delay)
    dir = doa.calc_doa(results)

    print(f"Heard speech from {dir}; directions recorded: {results}")
    new_dir = dir - 45
    print(f"Shifted servo by {new_dir}")
    ## Send angle to shift to arduino
    port.write(str(new_dir).encode())


q = queue.Queue()
devices = sd.query_devices()

port = serial.Serial(port=serial_port, baudrate=115200, timeout=.1)

# ============================ gigachat ==========================
llm = GigaChat(
        credentials=gigachat_creds,
        temperature=0.1,
        verify_ssl_certs=False,
        model="GigaChat-Pro"
    )

# ============================ camera ============================
camera = cv2.VideoCapture(2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

if camera.isOpened() != True:
  print("USB Camera Open Error!!!")
  sys.exit(0)

def capture():
  while True:
    print('== capture ==')
    time.sleep(0.5)
    ret, image = camera.read()
    if ret:
      break
  return image

# ============================ respeaker ============================
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

# ============================ speechkit ============================
session = Session.from_yandex_passport_oauth_token(oauth_token, catalog_id)
synthesizeAudio = SpeechSynthesis(session)
speechkit_voice = 'zahar'
sample_rate = 16000

def pyaudio_play_audio_function(audio_data, num_channels=1,
                                sample_rate=16000, chunk_size=4000) -> None:
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=num_channels,
        rate=sample_rate,
        output=True,
        frames_per_buffer=chunk_size
    )

    try:
        for i in range(0, len(audio_data), chunk_size):
            stream.write(audio_data[i:i + chunk_size])
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# ============================ main ============================

## Main code
try:
    model = vosk.Model("/path/to/vosk-model-ru")
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
                        #move_servo = threading.Thread(target=move_servo_to)
                        #move_servo.start()
                        move_servo_to()
                        dir = doa.get_doa(device)
                        print(f"Recognized \"{voice}\" from {dir}")
                        audio_data = synthesizeAudio.synthesize_stream(
                            text = 'Привет, слушаю тебя и готов выполнять команды' + '.0.', voice = speechkit_voice, format = 'lpcm', sampleRateHertz = sample_rate)
                        pyaudio_play_audio_function(audio_data, sample_rate = sample_rate)
                        q.queue.clear()

                    elif any(keyword in voice for keyword in keyword_vars2):
                        print(f"Recognized \"{voice}\"")
                        image = capture()
                        cv2.imwrite('/tmp/image.jpg', image)
                        file = llm.upload_file(open("/tmp/image.jpg", "rb"))
                        response = llm.invoke([
                                       HumanMessage(
                                           content="Что ты видишь? Начинай свой ответ так: Я вижу... Не используй в своем ответе такие слова как снимок, фотография, изображение и подобные! Это не фотография! Ты описываешь то, что ты реально видишь!",
                                           additional_kwargs={"attachments": [file.id_]}
                                       )
                                   ]).content
                        print(response)
                        audio_data = synthesizeAudio.synthesize_stream(
                            text = response + '.0.', voice = speechkit_voice, format = 'lpcm', sampleRateHertz = sample_rate)
                        pyaudio_play_audio_function(audio_data, sample_rate = sample_rate)
                        q.queue.clear()

except KeyboardInterrupt:
    print('\nDone')
