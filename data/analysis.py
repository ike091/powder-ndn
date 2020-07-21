import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="the name of the file to analyze", default="data.csv")

    args = parser.parse_args()

    data = pd.read_csv(args.filename)

    #  print(data)

    print(type(data['bitrate_kbps']))


    print(data['bitrate_kbps'].to_dict())


    plt.plot(range(0, 20), data['bitrate_kbps'])
    plt.ylabel("bitrate")
    plt.xlabel("trial #")
    plt.show()



main()
