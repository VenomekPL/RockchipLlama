
from rknnlite.api import RKNNLite
import sys

def inspect_api():
    rknn = RKNNLite()
    print("Attributes of RKNNLite:")
    for attr in dir(rknn):
        print(attr)

if __name__ == "__main__":
    inspect_api()
