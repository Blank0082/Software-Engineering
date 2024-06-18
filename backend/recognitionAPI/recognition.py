#!/usr/bin/env python
# coding: utf-8

import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import predictor
import evaluator
import paper_cut
import transform


def _loadTruth(test_file_path, truth_paths):
    truth_table = {}
    if os.path.isfile(truth_paths):
        with open(truth_paths, 'r', encoding='utf-8') as fr:
            truth_tables = fr.read()
        truth_tables = truth_tables.replace(' ', '')
        truth_tables = truth_tables.split('\n')
        truth_table = {}
        for truth in truth_tables:
            if len(truth.split(',')) != 2:
                continue
            key, value = truth.split(',')
            key = ((os.path.join(test_file_path, key)).replace('\\', '/'))
            key = key[1:] if key[0] == '.' else key
            truth_table[key] = value
    return truth_table


def _loadImage(test_path):
    # load image
    paths = []
    for root, dirs, files in os.walk(test_path):
        for name in files:
            image_path = os.path.join(root, name)
            if ('.info' in image_path) or ('jpg' not in image_path and 'png' not in image_path):
                continue
            paths.append(image_path)
    return paths


def predict(mymodel, test_path, class_path, truth_path):
    model = mymodel
    test_file_path = test_path
    test_truth_path = truth_path

    image_paths = _loadImage(test_file_path)
    groundTruths = _loadTruth(test_file_path, test_truth_path)

    # make prediction
    pred = predictor.predictor(model, class_path, image_paths, 5)
    predictions = pred.run()
    # print(predictions)

    # make evaluation
    eval = evaluator.evaluator(groundTruths, predictions)
    evaluations, predictions = eval.run()

    return evaluations, predictions


class MyEnsemble(nn.Module):
    def __init__(self, modelA, modelB, modelC, nb_classes=5716):
        super(MyEnsemble, self).__init__()
        self.modelA = modelA
        self.modelB = modelB
        self.modelC = modelC
        # self.modelD = modelD
        # Remove last linear layer
        self.modelA.classifier = nn.Identity()
        self.modelB.classifier = nn.Identity()
        self.modelC.classifier = nn.Identity()
        # self.modelD.classifier = nn.Identity()

        # Create new classifier
        self.classifier = nn.Linear((3 * 2208), nb_classes)

    def forward(self, x):
        x1 = self.modelA(x.clone())  # clone to make sure x is not changed by inplace methods
        x1 = x1.view(x1.size(0), -1)
        x2 = self.modelB(x)
        x2 = x2.view(x2.size(0), -1)
        x3 = self.modelC(x)
        x3 = x3.view(x3.size(0), -1)
        # x4 = self.modelD(x)
        # x4 = x4.view(x4.size(0), -1)
        x = torch.cat((x1, x2, x3), dim=1)

        x = self.classifier(F.relu(x))
        return x


# modelA = torch.load('./test/densenet.pth')  # base
# modelB = torch.load('./test/SP1.pth')  # 高斯
# modelC = torch.load('./test/GS3.pth')  # S&p
# modelD = torch.load('./test/Edge-F.pth')  # merge

# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# # model = MyEnsemble(modelA, modelB, modelC, modelD).to(device)
# model = torch.load("./model/ensamble_stacking.pth").to(device)
#
# paper_cutter = paper_cut.GridSplitPaper(HLine=19, VLine=41, girdWidth1=71, girdWidth2=22, girdHeight=71)
# input_path = "./input/111091441-C110151129-1.jpg"
#
# transform_path = './transform'
# output_path = './output'  # 待辨識的資料集路徑
# class_path = './api/classes.txt'  # 資料集的類別
# truth_path = './api/test_truth.txt'  # 資料集的真實標籤
#
# filename = os.path.splitext(os.path.basename(input_path))[0]
# print(filename)
# t = transform.Transformer(input_path)
# success_t = t.run(transform_path)
# for filename in os.listdir(transform_path):
#     if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
#         input_path_img = os.path.join(transform_path, filename)
#         success_c = paper_cutter.split(input_path_img, output_path)
#
# evaluations, predictions = predict(model, output_path, class_path, truth_path)
#
# first_classes = [pred['predicts'][1]['class'] for pred in predictions]
#
# result_string = ''.join(first_classes)
# print(result_string)

