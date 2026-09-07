import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.preprocessing import LabelEncoder
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import transforms

device = "cuda" if torch.cuda.is_available() else "cpu"


image_path = []
lables = []


for i in os.listdir(
    "/home/nishant/Nishant_stuff/pytorch_tuto/image_classification/dataset"
):
    print(i)
    for label in os.listdir(
        f"/home/nishant/Nishant_stuff/pytorch_tuto/image_classification/dataset/{i}"
    ):
        print(label)
        for image in os.listdir(f"/home/nishant/Nishant_stuff/pytorch_tuto/image_classification/dataset/{i}/{label}"):
            print(image)
            break
        break
    break
