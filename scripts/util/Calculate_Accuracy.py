import random
import numpy as np
import re
from sklearn.utils.linear_assignment_ import linear_assignment
import warnings

warnings.filterwarnings("ignore")


GT = 0
FP = 0
FN = 0
TP = 0


def reset_numbers():
    global GT
    global FP
    global FN
    global TP
    GT = 0
    FP = 0
    FN = 0
    TP = 0


def iou(bb_det,bb_gt):
    xx1 = np.maximum(bb_det[0],bb_gt[0])
    yy1 = np.maximum(bb_det[1],bb_gt[1])
    xx2 = np.minimum(bb_det[2],bb_gt[2])
    yy2 = np.minimum(bb_det[3],bb_gt[3])
    w = np.maximum(0.,xx2 - xx1)
    h = np.maximum(0.,yy2 - yy1)
    wh = w * h
    o = wh / ((bb_det[2]-bb_det[0])*(bb_det[3]-bb_det[1]) + (bb_gt[2]-bb_gt[0])*(bb_gt[3]-bb_gt[1]) - wh)
    return o


def get_accuracy(gt_boxes,det_boxes):
    global GT
    global FP
    global FN
    global TP

    if (len(gt_boxes)==0 and len(det_boxes)==0):
        return
    if (len(gt_boxes)==0 and len(det_boxes)!=0):
        FP += len(det_boxes)
        return
    if (len(det_boxes)==0 and len(gt_boxes)!=0):
        FN +=len(gt_boxes)
        GT +=len(gt_boxes)
        return
    GT+=len(gt_boxes)


    iou_matrix =  np.zeros((len(det_boxes),len(gt_boxes)),dtype=np.float32)
    for d,det in enumerate(det_boxes):
        #print(det)
        #bb_det = [int(det[2]),int(det[3]),int(det[2])+int(det[4]),int(det[3])+int(det[5])]
        for g,gt in enumerate(gt_boxes):
            #bb_gt = [int(gt[2]),int(gt[3]),int(gt[2])+int(gt[4]),int(gt[3])+int(gt[5])]
            iou_matrix[d,g] = iou(det,gt)
            #print(d,g,iou_matrix[d,g])
    #print(iou_matrix)
    matched_indices = linear_assignment(-iou_matrix)
    #print(matched_indices)
    unmatched_dets = [];

    for d,det in enumerate(det_boxes):
        if (d not in matched_indices[:,0]):
            unmatched_dets.append(d)
    unmatched_gts = []
    for g,gt in enumerate(gt_boxes):
        if (g not in matched_indices[:,1]):
            unmatched_gts.append(g)

    matches = []
    iou_threshold = 0.50

    for m in matched_indices:
        if (iou_matrix[m[0],m[1]]<iou_threshold):
            unmatched_dets.append(m[0])
            unmatched_gts.append(m[1])
        else:
            matches.append(m.reshape(1,2))
    #print(len(matches),len(unmatched_dets),len(unmatched_gts))

    TP+=len(matches)
    FP+=len(unmatched_dets)
    FN+=len(unmatched_gts)
    # print("Accuracy: ",TP,FP,FN,GT)


def get_accuracy_metrics():
    global TP
    global FP
    global FN
    global GT
    Precision = float(TP)/(TP+FP)*100.0;
    Recall = float(TP)/(TP+FN)*100.0;
    F1Score = 2*Precision*Recall/(Precision+Recall)
    print("Precision: ",Precision)
    print("Recall: ",Recall)
    print("F Score: ",F1Score)


