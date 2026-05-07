import torch.nn as nn
import torch
import torch.nn.functional as F

def autopad_MSHA(k, p=None, d=1):  # kernel, padding, dilation
    """Pad to 'same' shape outputs."""
    if d > 1:
        k = d * (k - 1) + 1 if isinstance(k, int) else [d * (x - 1) + 1 for x in k]  # actual kernel-size
    if p is None:
        p = k // 2 if isinstance(k, int) else [x // 2 for x in k]  # auto-pad
    return p


class Conv_withBN(nn.Module):
    """Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)."""

    default_act = nn.SiLU()  # default activation

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        """Initialize Conv layer with given arguments including activation."""
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad_MSHA(k, p, d), groups=g, dilation=d, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x):
        """Apply convolution, batch normalization and activation to input tensor."""
        return self.act(self.bn(self.conv(x)))

    def forward_fuse(self, x):
        """Perform transposed convolution of 2D data."""
        return self.act(self.conv(x))

class Conv_withoutBN(nn.Module):
    # Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)
    default_act = nn.SiLU()  # default activation

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad_MSHA(k, p, d), groups=g, dilation=d, bias=False)
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x):
        return self.act(self.conv(x))

class BasicConv_1_3(nn.Module):
    def __init__(self, in_planes, out_planes, kernel_size, stride=1, padding=0, dilation=1, groups=1, relu=True,
                 bn=True, bias=False):
        super(BasicConv_1_3, self).__init__()
        self.out_channels = out_planes
        self.conv = nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=padding,
                              dilation=dilation, groups=groups, bias=bias)
        self.bn = nn.BatchNorm2d(out_planes, eps=1e-5, momentum=0.01, affine=True) if bn else None
        self.relu = nn.ReLU(inplace=True) if relu else None

    def forward(self, x):
        x = self.conv(x)
        if self.bn is not None:
            x = self.bn(x)
        if self.relu is not None:
            x = self.relu(x)
        return x

class MSHA(nn.Module):
    def __init__(self, dim, num_heads=8,
                 attn_ratio=0.5):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.key_dim = int(self.head_dim * attn_ratio)
        self.scale = self.key_dim ** -0.5
        nh_kd = nh_kd = self.key_dim * num_heads
        h = dim + nh_kd * 2
        self.qkv = Conv_withBN(dim, h, 1, act=False)
        self.proj = Conv_withBN(dim, dim, 1, act=False)
        self.pe = Conv_withBN(dim, dim, 3, 1, g=dim, act=False)

    def forward(self, x):
        B, C, H, W = x.shape
        N = H * W
        qkv = self.qkv(x)
        q, k, v = qkv.view(B, self.num_heads, self.key_dim*2 + self.head_dim, N).split([self.key_dim, self.key_dim, self.head_dim], dim=2)

        attn = (
            (q.transpose(-2, -1) @ k) * self.scale
        )
        attn = attn.softmax(dim=-1)
        x = (v @ attn.transpose(-2, -1)).view(B, C, H, W) + self.pe(v.reshape(B, C, H, W))
        x = self.proj(x)
        return x

class SAAM(nn.Module):
    def __init__(self, in_channels, reduction=1, conv_cfg=None):
        super().__init__()
        self.c = int(in_channels*0.5)
        self.in_channels = in_channels
        self.inter_channels = max(in_channels // reduction, 1)
        #conv_params = dict(k=1, conv_cfg=conv_cfg, act_cfg=None)

        self.msha = MSHA(self.in_channels, attn_ratio=0.5, num_heads=self.c // 8)

        self.conv1_3 = BasicConv_1_3(self.in_channels, (self.in_channels // 2) * 3, kernel_size=(1, 3), stride=1, padding=(0, 1))
        self.conv3_1 = BasicConv_1_3((self.in_channels // 2) * 3, self.in_channels, kernel_size=(3, 1), stride=1, padding=(1, 0))

        self.a = Conv_withBN(self.in_channels, 1, 1, 1)
        self.k = Conv_withBN(self.in_channels, 1, 1, 1)
        self.v = Conv_withBN(self.in_channels, self.inter_channels, 1, 1)
        self.m = Conv_withoutBN(self.inter_channels, self.in_channels, 1, 1)

    def forward(self, x):
        #x = self.msha(x)

        n, c = x.size(0), self.inter_channels

        #branch0
        a_1, a_2 = x.split((self.c, self.c), dim=1)
        a_1 = F.adaptive_max_pool2d(a_1, output_size=1)
        a_2 = F.adaptive_avg_pool2d(a_2, output_size=1)
        a = torch.cat((a_1, a_2), dim=1)
        a = F.sigmoid(a) * x
        # a: [N, 1, H, W]
        a = self.a(x).softmax(1)

        #branch1
        x_ = self.conv1_3(x)
        x_ = self.conv3_1(x_)
        #v [N, 1, C, HW]
        v = self.v(x_).view(n, 1, c, -1)
        #k [N, 1, HW, 1]
        k = self.k(x_).view(n, 1, -1, 1).softmax(2)

        y = torch.matmul(v, k).view(n, c, 1, 1)
        y = self.m(y) * a

        return x+y


class SAAM_Head(nn.Module):
    def __init__(self, in_channels, reduction=1, conv_cfg=None):
        super().__init__()
        self.c = int(in_channels*0.5)
        self.in_channels = in_channels
        self.inter_channels = max(in_channels // reduction, 1)
        #conv_params = dict(k=1, conv_cfg=conv_cfg, act_cfg=None)

        self.msha = MSHA(self.c, attn_ratio=0.5, num_heads=self.c // 64)

        self.conv1_3 = BasicConv_1_3(self.in_channels, (self.in_channels // 2) * 3, kernel_size=(1, 3), stride=1, padding=(0, 1))
        self.conv3_1 = BasicConv_1_3((self.in_channels // 2) * 3, self.in_channels, kernel_size=(3, 1), stride=1, padding=(1, 0))

        self.a = Conv_withBN(self.in_channels, 1, 1, 1)
        self.k = Conv_withBN(self.in_channels, 1, 1, 1)
        self.v = Conv_withBN(self.in_channels, self.inter_channels, 1, 1)
        self.m = Conv_withoutBN(self.inter_channels, self.in_channels, 1, 1)

    def forward(self, x):
        n, c = x.size(0), self.inter_channels

        #branch0
        a_1, a_2 = x.split((self.c, self.c), dim=1)
        a_1 = F.adaptive_max_pool2d(a_1, output_size=1)
        a_2 = F.adaptive_avg_pool2d(a_2, output_size=1)
        a = torch.cat((a_1, a_2), dim=1)
        a = F.sigmoid(a) * x
        # a: [N, 1, H, W]
        a = self.a(x).softmax(1)

        #branch1
        x_ = self.conv1_3(x)
        x_ = self.conv3_1(x_)
        #v [N, 1, C, HW]
        v = self.v(x_).view(n, 1, c, -1)
        #k [N, 1, HW, 1]
        k = self.k(x_).view(n, 1, -1, 1).softmax(2)

        y = torch.matmul(v, k).view(n, c, 1, 1)
        y = self.m(y) * a

        return x+y





