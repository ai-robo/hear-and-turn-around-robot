from tuning import Tuning
import usb.core
import usb.util
import time

def find_respeaker():
    return usb.core.find(idVendor=0x2886, idProduct=0x0018)

def get_doa(device):
    Mic_tuning = Tuning(device)
    return Mic_tuning.direction

def calc_doa(doa_results: list):
    return round(sum(doa_results) / len(doa_results))


if __name__ == "__main__":
    dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    if dev:
        Mic_tuning = Tuning(dev)
#         print(Mic_tuning.direction)
        while True:
            try:
                #print(Mic_tuning.direction)
                dirs = []
                for i in range(0, 5):
                    dirs.append(Mic_tuning.direction)
                    time.sleep(.5)
                print(f"Result doa (arithmetic average): {calc_doa(dirs)}; direction recorded: {dirs}")

            except KeyboardInterrupt:
                break
