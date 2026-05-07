from collections import OrderedDict

import torch
import torch.nn as nn
import torch.nn.functional as F



def BasicConv(filter_in, filter_out, kernel_size, stride=1, pad=None):
    if not pad:
        pad = (kernel_size - 1) // 2 if kernel_size else 0
    else:
        pad = pad
    return nn.Sequential(OrderedDict([
        ("conv", nn.Conv2d(filter_in, filter_out, kernel_size=kernel_size, stride=stride, padding=pad, bias=False)),
        ("bn", nn.BatchNorm2d(filter_out)),
        ("relu", nn.ReLU(inplace=True)),
    ]))


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, filter_in, filter_out):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(filter_in, filter_out, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(filter_out, momentum=0.1)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(filter_out, filter_out, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(filter_out, momentum=0.1)

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out += residual
        out = self.relu(out)

        return out


class Upsample(nn.Module):
    def __init__(self, in_channels, out_channels, scale_factor=2):
        super(Upsample, self).__init__()

        self.upsample = nn.Sequential(
            BasicConv(in_channels, out_channels, 1),
            nn.Upsample(scale_factor=scale_factor, mode='bilinear')
        )

        # carafe
        # from mmcv.ops import CARAFEPack
        # self.upsample = nn.Sequential(
        #     BasicConv(in_channels, out_channels, 1),
        #     CARAFEPack(out_channels, scale_factor=scale_factor)
        # )

    def forward(self, x):
        x = self.upsample(x)

        return x


class Downsample_x2(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Downsample_x2, self).__init__()

        self.downsample = nn.Sequential(
            BasicConv(in_channels, out_channels, 2, 2, 0)
        )

    def forward(self, x, ):
        #print(f'Down input: {x.shape}')
        x = self.downsample(x)
        #print(f'Down output: {x.shape}')
        return x


class Downsample_x4(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Downsample_x4, self).__init__()

        self.downsample = nn.Sequential(
            BasicConv(in_channels, out_channels, 4, 4, 0)
        )

    def forward(self, x, ):
        x = self.downsample(x)

        return x


class Downsample_x8(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Downsample_x8, self).__init__()

        self.downsample = nn.Sequential(
            BasicConv(in_channels, out_channels, 8, 8, 0)
        )

    def forward(self, x, ):
        x = self.downsample(x)

        return x


class ASFF_2(nn.Module):
    def __init__(self, inter_dim=512):
        super(ASFF_2, self).__init__()

        self.inter_dim = inter_dim
        compress_c = 8

        self.weight_level_1 = BasicConv(self.inter_dim, compress_c, 1, 1)
        self.weight_level_2 = BasicConv(self.inter_dim, compress_c, 1, 1)

        self.weight_levels = nn.Conv2d(compress_c * 2, 2, kernel_size=1, stride=1, padding=0)

        self.conv = BasicConv(self.inter_dim, self.inter_dim, 3, 1)

    def forward(self, input1, input2):
        print(input1.shape, input2.shape)
        level_1_weight_v = self.weight_level_1(input1)
        level_2_weight_v = self.weight_level_2(input2)

        levels_weight_v = torch.cat((level_1_weight_v, level_2_weight_v), 1)
        levels_weight = self.weight_levels(levels_weight_v)
        levels_weight = F.softmax(levels_weight, dim=1)

        fused_out_reduced = input1 * levels_weight[:, 0:1, :, :] + \
                            input2 * levels_weight[:, 1:2, :, :]

        out = self.conv(fused_out_reduced)
        print(out.shape)
        exit()

        return out


class ASFF_3(nn.Module):
    def __init__(self, inter_dim=512):
        super(ASFF_3, self).__init__()

        self.inter_dim = inter_dim
        compress_c = 8

        self.weight_level_1 = BasicConv(self.inter_dim, compress_c, 1, 1)
        self.weight_level_2 = BasicConv(self.inter_dim, compress_c, 1, 1)
        self.weight_level_3 = BasicConv(self.inter_dim, compress_c, 1, 1)

        self.weight_levels = nn.Conv2d(compress_c * 3, 3, kernel_size=1, stride=1, padding=0)

        self.conv = BasicConv(self.inter_dim, self.inter_dim, 3, 1)

    def forward(self, input1, input2, input3):
        level_1_weight_v = self.weight_level_1(input1)
        level_2_weight_v = self.weight_level_2(input2)
        level_3_weight_v = self.weight_level_3(input3)

        levels_weight_v = torch.cat((level_1_weight_v, level_2_weight_v, level_3_weight_v), 1)
        levels_weight = self.weight_levels(levels_weight_v)
        levels_weight = F.softmax(levels_weight, dim=1)

        fused_out_reduced = input1 * levels_weight[:, 0:1, :, :] + \
                            input2 * levels_weight[:, 1:2, :, :] + \
                            input3 * levels_weight[:, 2:, :, :]

        out = self.conv(fused_out_reduced)

        return out


class ASFF_4(nn.Module):
    def __init__(self, inter_dim=512):
        super(ASFF_4, self).__init__()

        self.inter_dim = inter_dim
        compress_c = 8

        self.weight_level_0 = BasicConv(self.inter_dim, compress_c, 1, 1)
        self.weight_level_1 = BasicConv(self.inter_dim, compress_c, 1, 1)
        self.weight_level_2 = BasicConv(self.inter_dim, compress_c, 1, 1)
        self.weight_level_3 = BasicConv(self.inter_dim, compress_c, 1, 1)

        self.weight_levels = nn.Conv2d(compress_c * 4, 4, kernel_size=1, stride=1, padding=0)

        self.conv = BasicConv(self.inter_dim, self.inter_dim, 3, 1)

    def forward(self, input0, input1, input2, input3):
        level_0_weight_v = self.weight_level_0(input0)
        level_1_weight_v = self.weight_level_1(input1)
        level_2_weight_v = self.weight_level_2(input2)
        level_3_weight_v = self.weight_level_3(input3)

        levels_weight_v = torch.cat((level_0_weight_v, level_1_weight_v, level_2_weight_v, level_3_weight_v), 1)
        levels_weight = self.weight_levels(levels_weight_v)
        levels_weight = F.softmax(levels_weight, dim=1)

        fused_out_reduced = input0 * levels_weight[:, 0:1, :, :] + \
                            input1 * levels_weight[:, 1:2, :, :] + \
                            input2 * levels_weight[:, 2:3, :, :] + \
                            input3 * levels_weight[:, 3:, :, :]

        out = self.conv(fused_out_reduced)

        return out