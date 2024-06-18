#!/usr/bin/env python
# coding: utf-8

# In[1]:


import cv2
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

from torchvision import models, transforms
from PIL import Image



class predictor():
    def __init__(self, model, class_path, test_paths, top):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.class_path = class_path
        self.test_paths = test_paths
        self.top = top
        self.detail = []
        # load model
        # self.model = self._load_model()
        # load class names
        with open(self.class_path, 'r', encoding='utf8') as f:
            self.class_names = (f.read()).split('\n')
        self.output_names = sorted([str(i) for i in range(len(self.class_names))])
        # print('success-----------------------------------------------------------')

    def _load_model(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model = torch.load(self.model_path, map_location=self.device)
        return model

    def _normalize(self, img):
        data_transforms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((64, 64)),
            transforms.Grayscale(num_output_channels=3),
            transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),

        ])
        return data_transforms(img)

    def _predict(self, batch_img):
        self.model.eval()
        prediction = self.model(batch_img)
        prediction = F.softmax(prediction, dim=1)
        # select top n result
        prediction = prediction.cpu()
        prediction = prediction.detach().numpy()
        predIndex = np.argsort(-prediction)[:, :self.top]
        predProba = [prediction[batch][predIndex[batch]] for batch in range(prediction.shape[0])]
        return predIndex, predProba

    def _decode(self, index):
        return self.class_names[int(self.output_names[index])]

    def run(self):
        predictions = []
        if len(self.test_paths) == 0:
            return predictions

        # prepare testset
        all_images = []
        for image_path in self.test_paths:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_array = np.frombuffer(image_data, np.uint8)
            try:
                img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            except Exception as e:
                print("Error decoding image:", str(e))
            img = self._normalize(img)
            all_images.append(img)
        # for image_path in tqdm(self.test_paths):
        #     img = cv2.imread(image_path)
        #     img = self._normalize(img)
        #     all_images.append(img)

        batch_size = 32
        images_batch = []
        predIndex = []
        predProba = []

        # Use tqdm to create a progress bar for the loop
        for i in range(0, len(all_images), batch_size):
            images_batch = all_images[i:i + batch_size]
            images_batch = torch.stack(images_batch)
            images_batch = images_batch.to(self.device)
            Index, Proba = self._predict(images_batch)
            for i in Index:
                predIndex.append(i)
            for j in Proba:
                predProba.append(j)

        # decode prediction's class
        for index, predImg in enumerate(predIndex):
            predicts = {}
            path = self.test_paths[index]
            for topIndex, top in enumerate(predImg):
                pclass = self._decode(top)
                probability = round(predProba[index][topIndex] * 100, 2)
                predicts[topIndex + 1] = {'class': pclass, 'probability': str(probability) + '%'}
            predictions.append({
                'filename': (path.replace('\\', '/')).split('/')[-1],
                'path': (path.replace('\\', '/'))[1:] if path[0] == '.' else (path.replace('\\', '/')),
                'predicts': predicts
            })

        return predictions
