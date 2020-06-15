import torch
import torch.nn as nn
import torch.nn.functional as F

def _compute_cross_entropy_loss(input, target):
    input = torch.log_softmax(input, dim = 1)
    loss = torch.sum(input * target, dim = 1, keepdim = False)
    loss = -torch.mean(loss, dim = 0, keepdim = False)
    return loss

def _compute_hinton_loss(input, target):
    T = 2
    input = torch.log_softmax(input/T, dim = 1)
    target = torch.softmax(target/T, dim = 1)
    loss = torch.sum(input * target, dim = 1, keepdim = False)
    loss = -torch.mean(loss, dim = 0, keepdim = False)
    return loss

def _compute_bce_loss(input, target):
    crit = nn.BCEWithLogitsLoss(reduction = "mean")
    return crit(input, target)

def _compute_icarl_loss(input, target):
    crit = nn.BCEWithLogitsLoss(reduction = "mean")
    target = nn.Sigmoid()(target)
    return crit(input, target)

def _compute_kldiv_loss(input, target):
    crit = .nn.KLDivLoss(reduction = "mean")
    input = torch.log_softmax(input, dim = 1)
    target = torch.softmax(target, dim = 1)
    return crit(input, target)

def _compute_lfc_loss(input, target):
    input = F.normalize(input, p = 2)
    target = F.normalize(target, p = 2)
    cosine_similarity = torch.sum(input * target, dim = 1)
    loss = torch.mean(1 - cosine_similarity, dim = 0)
    return loss

class CustomizedLoss():
    def __init__(self, classification, distillation):
        self.classification = classification
        self.distillation = distillation
        self.loss_computer = {
        "bce": _compute_bce_loss,
        "icarl": _compute_icarl_loss,
        "ce": _compute_cross_entropy_loss,
        "hinton": _compute_hinton_loss,
        "kldiv": _compute_kldiv_loss,
        "lfc": _compute_lfc_loss
        }

    def __call__(self, class_input, class_target, dist_input, dist_target):
        # need this to handle the variation case, when normally the class_loss is "icarl"
        # but in the first step is "bce"
        if self.classification == "icarl" and dist_input is None:
            class_loss = self.loss_computer["bce"](class_input, class_target)
        else:
            class_loss = self.loss_computer[self.classification](class_input, class_target)

        if self.distillation is not None and dist_input is not None and dist_target is not None:
            n_new_classes = class_input.shape[1]
            n_old_classes = dist_input.shape[1]
            class_ratio = n_new_classes/(n_new_classes+n_old_classes)
            dist_ratio = 1 - class_ratio

            dist_loss =  self.loss_computer[self.distillation](dist_input, dist_target)
            tot_loss = class_ratio*class_loss + dist_ratio*dist_loss
            return tot_loss
        else:
            return class_loss