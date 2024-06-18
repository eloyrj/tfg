import random
import numpy as np
import torch
from ultralytics import YOLO
import yaml


seed = 1
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed(seed)

# Load a model
model = YOLO('yolov8n.pt')  # load a pretrained model (recommended for training)


results = model.train(data="C:/Users/corte/Documents/GitHub/tfgProject/aircrafts_datashet/data.yaml", epochs=100, imgsz=640)