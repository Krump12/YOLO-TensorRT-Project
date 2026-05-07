import torch.nn as nn
import torch
import torch.nn.functional as F
import math

class GhostModule(nn.Module):
    def __init__(self, inp, oup, kernel_size=1, ratio=2, dw_size=3, stride=1, relu=True):
        super(GhostModule, self).__init__()
        self.oup = oup
        init_channels = math.ceil(oup / ratio)
        new_channels = init_channels*(ratio-1)

        self.primary_conv = nn.Sequential(
            nn.Conv2d(inp, init_channels, kernel_size, stride, kernel_size//2, bias=False),
            nn.BatchNorm2d(init_channels),
            nn.ReLU(inplace=True) if relu else nn.Sequential(),
        )

        self.cheap_operation = nn.Sequential(
            nn.Conv2d(init_channels, new_channels, dw_size, 1, dw_size//2, groups=init_channels, bias=False),
            nn.BatchNorm2d(new_channels),
            nn.ReLU(inplace=True) if relu else nn.Sequential(),
        )

    def forward(self, x):
        x1 = self.primary_conv(x)
        x2 = self.cheap_operation(x1)
        out = torch.cat([x1,x2], dim=1)
        return out[:,:self.oup,:,:]

class ASPPConv(nn.Module):
    def __init__(self, in_channels, out_channels, dilation):
        super(ASPPConv, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=dilation, dilation=dilation, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU()
        )

    def forward(self, x):
        return self.conv(x)

# def autopad_FPN(k, p=None, d=1):  # kernel, padding, dilation
#     """Pad to 'same' shape outputs."""
#     if d > 1:
#         k = d * (k - 1) + 1 if isinstance(k, int) else [d * (x - 1) + 1 for x in k]  # actual kernel-size
#     if p is None:
#         p = k // 2 if isinstance(k, int) else [x // 2 for x in k]  # auto-pad
#     return p
#
#
# class Conv_FPN(nn.Module):
#     """Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)."""
#
#     default_act = nn.SiLU()  # default activation
#
#     def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
#         """Initialize Conv layer with given arguments including activation."""
#         super().__init__()
#         self.conv = nn.Conv2d(c1, c2, k, s, autopad_FPN(k, p, d), groups=g, dilation=d, bias=False)
#         self.bn = nn.BatchNorm2d(c2)
#         self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()
#
#     def forward(self, x):
#         """Apply convolution, batch normalization and activation to input tensor."""
#         return self.act(self.bn(self.conv(x)))
#
#     def forward_fuse(self, x):
#         """Perform transposed convolution of 2D data."""
#         return self.act(self.conv(x))


class AtFPN(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(AtFPN, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        self.GhostModule = GhostModule(self.in_channels, self.out_channels)
        self.conv = nn.Conv2d(self.in_channels, self.out_channels, kernel_size=3, padding=1, stride=2)
        #self.conv = Conv_FPN(self.in_channels, self.out_channels, k=3, s=2,act=False)
        self.conv_1 = nn.Sequential(
            nn.Conv2d(self.in_channels * 4, self.out_channels, kernel_size=1),
            #Conv_FPN(self.in_channels * 4, self.out_channels, k=1, s=1)
            nn.BatchNorm2d(self.out_channels, eps=1e-5, momentum=0.01, affine=True),
            nn.ReLU(inplace=True)
        )
        self.at_conv_1 = ASPPConv(in_channels, out_channels, 6)
        self.at_conv_2 = ASPPConv(in_channels, out_channels, 12)

        #self.upsample = nn.Upsample(scale_factor=2, mode='nearest')

        #self.upsample = nn.Upsample(size=(hight, weight), mode='bilinear', align_corners=False)

    def forward(self, x):
        b, c, h, w = x.size()

        #branch0
        x0_ = self.GhostModule(x)

        #branch1
        x1 = self.conv(x)
        x1_ = self.at_conv_1(x1)
        _, _, h_, w_ = x1_.size()

        #branch2
        x2 = self.conv(x1)
        x2_ = self.at_conv_2(x2)

        #upsample
        #x2_ = self.upsample(x2_)
        x2_ = F.interpolate(x2_, size=(h_, w_), mode='bilinear', align_corners=False)

        x_ = torch.cat((x2_, x1), dim=1)
        x_ = torch.cat((x_, x1_), dim=1)

        x_ = F.interpolate(x_, size=(h, w), mode='bilinear', align_corners=False)
        #x_ = self.upsample(x_)

        x_out = torch.cat((x_, x0_), dim=1)

        x = self.conv_1(x_out)

        return x

class StateRM(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super(StateRM, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 1)

    def forward(self, state):
        #计算注意力分数
        attention_weights = F.softmax(self.fc2(F.relu(self.fc1(state))), dim=1)
        #加权求和得到新状态表示
        weight_state = torch.mul(state, attention_weights).sum(dim=1)
        return weight_state

class ASCSM(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ASCSM, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        self.GhostModule = GhostModule(self.in_channels, self.out_channels)
        self.conv = nn.Conv2d(self.in_channels, self.out_channels, kernel_size=3, padding=1, stride=2)
        #self.conv = Conv_FPN(self.in_channels, self.out_channels, k=3, s=2,act=False)
        self.conv_1 = nn.Sequential(
            nn.Conv2d(self.in_channels * 4, self.out_channels, kernel_size=1),
            #Conv_FPN(self.in_channels * 4, self.out_channels, k=1, s=1)
            nn.BatchNorm2d(self.out_channels, eps=1e-5, momentum=0.01, affine=True),
            nn.ReLU(inplace=True)
        )
        self.at_conv_1 = ASPPConv(in_channels, out_channels, 6)
        self.at_conv_2 = ASPPConv(in_channels, out_channels, 12)
        self.at_conv_3 = ASPPConv(in_channels, out_channels, 18)

        self.state_rm = StateRM(in_channels, in_channels*2)

        #self.upsample = nn.Upsample(scale_factor=2, mode='nearest')

        #self.upsample = nn.Upsample(size=(hight, weight), mode='bilinear', align_corners=False)

    def forward(self, x):
        b, c, h, w = x.size()
        #branch0
        x0 = self.GhostModule(x)

        #branch1
        x1 = self.at_conv_1(x)

        #branch2
        x2 = self.at_conv_2(x)

        #branch3
        x3 = self.at_conv_3(x)

        x_0 = torch.cat((x0, x1, x2, x3), dim=1)
        x_1 = self.conv_1(x_0)
        #
        state = x_1.mean(dim=[2, 3])
        #state = torch.randn(b, self.in_channels)
        weighted_state = self.state_rm(state)
        weighted_state = weighted_state.view(b, 1, 1, 1).expand(-1, c, h, w)

        x_out = x+weighted_state

        #

        return x_out

class ASCSM_Back(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ASCSM_Back, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        self.GhostModule = GhostModule(self.in_channels, self.out_channels)
        self.conv = nn.Conv2d(self.in_channels, self.out_channels, kernel_size=3, padding=1, stride=2)
        #self.conv = Conv_FPN(self.in_channels, self.out_channels, k=3, s=2,act=False)
        self.conv_1 = nn.Sequential(
            nn.Conv2d(self.in_channels * 4, self.out_channels, kernel_size=1),
            #Conv_FPN(self.in_channels * 4, self.out_channels, k=1, s=1)
            nn.BatchNorm2d(self.out_channels, eps=1e-5, momentum=0.01, affine=True),
            nn.ReLU(inplace=True)
        )
        self.at_conv_1 = ASPPConv(in_channels, out_channels, 6)
        self.at_conv_2 = ASPPConv(in_channels, out_channels, 12)
        self.at_conv_3 = ASPPConv(in_channels, out_channels, 18)

        self.state_rm = StateRM(in_channels, in_channels*2)

        #self.upsample = nn.Upsample(scale_factor=2, mode='nearest')

        #self.upsample = nn.Upsample(size=(hight, weight), mode='bilinear', align_corners=False)

    def forward(self, x):
        b, c, h, w = x.size()
        #branch0
        x0 = self.GhostModule(x)

        #branch1
        x1 = self.at_conv_1(x)

        #branch2
        x2 = self.at_conv_2(x)

        #branch3
        x3 = self.at_conv_3(x)

        x_0 = torch.cat((x0, x1, x2, x3), dim=1)
        x_1 = self.conv_1(x_0)
        #
        state = x_1.mean(dim=[2, 3])
        #state = torch.randn(b, self.in_channels)
        weighted_state = self.state_rm(state)
        weighted_state = weighted_state.view(b, 1, 1, 1).expand(-1, c, h, w)

        x_out = x+weighted_state

        x_out = x_out + x

        return x_out

class Attn(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Attn, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        self.state_rm = StateRM(in_channels, in_channels*2)

        #self.upsample = nn.Upsample(scale_factor=2, mode='nearest')

        #self.upsample = nn.Upsample(size=(hight, weight), mode='bilinear', align_corners=False)

    def forward(self, x):
        b, c, h, w = x.size()

        state = x.mean(dim=[2, 3])
        #state = torch.randn(b, self.in_channels)
        weighted_state = self.state_rm(state)
        weighted_state = weighted_state.view(b, 1, 1, 1).expand(-1, c, h, w)

        x_out = x+weighted_state

        #

        return x_out


class simam_module(torch.nn.Module):
    def __init__(self, channels=None, e_lambda=1e-4):
        super(simam_module, self).__init__()

        self.activaton = nn.Sigmoid()
        self.e_lambda = e_lambda

    def __repr__(self):
        s = self.__class__.__name__ + '('
        s += ('lambda=%f)' % self.e_lambda)
        return s

    def forward(self, x):
        b, c, h, w = x.size()

        n = w * h - 1

        x_minus_mu_square = (x - x.mean(dim=[2, 3], keepdim=True)).pow(2)
        y = x_minus_mu_square / (4 * (x_minus_mu_square.sum(dim=[2, 3], keepdim=True) / n + self.e_lambda)) + 0.5

        return x * self.activaton(y)

class ASCSM_SimAM(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ASCSM_SimAM, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        self.GhostModule = GhostModule(self.in_channels, self.out_channels)
        self.conv = nn.Conv2d(self.in_channels, self.out_channels, kernel_size=3, padding=1, stride=2)
        #self.conv = Conv_FPN(self.in_channels, self.out_channels, k=3, s=2,act=False)
        self.conv_1 = nn.Sequential(
            nn.Conv2d(self.in_channels * 4, self.out_channels, kernel_size=1),
            #Conv_FPN(self.in_channels * 4, self.out_channels, k=1, s=1)
            nn.BatchNorm2d(self.out_channels, eps=1e-5, momentum=0.01, affine=True),
            nn.ReLU(inplace=True)
        )
        self.at_conv_1 = ASPPConv(in_channels, out_channels, 6)
        self.at_conv_2 = ASPPConv(in_channels, out_channels, 12)
        self.at_conv_3 = ASPPConv(in_channels, out_channels, 18)

        self.attn = simam_module()

    def forward(self, x):
        b, c, h, w = x.size()
        #branch0
        x0 = self.GhostModule(x)

        #branch1
        x1 = self.at_conv_1(x)

        #branch2
        x2 = self.at_conv_2(x)

        #branch3
        x3 = self.at_conv_3(x)

        x_0 = torch.cat((x0, x1, x2, x3), dim=1)
        x_1 = self.conv_1(x_0)

        x_1 = self.attn(x_1)

        x_out = x + x_1

        return x_out


