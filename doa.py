from tuning import Tuning
import usb.core
import usb.util
#import time

def find_respeaker():
    return usb.core.find(idVendor=0x2886, idProduct=0x0018)

def get_doa(device):
    Mic_tuning = Tuning(device)
    return Mic_tuning.direction

def calc_direction():
    ...


# if __name__ == "__main__":
#
#     dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
#
#     if dev:
#         Mic_tuning = Tuning(dev)
#         print(Mic_tuning.direction)
#         while True:
#             try:
#                 print(Mic_tuning.direction)
#                 time.sleep(1)
#             except KeyboardInterrupt:
#                 break
