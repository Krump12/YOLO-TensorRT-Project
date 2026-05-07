import torch.nn as nn
import torch

class Squeeze_Conv(nn.Module):

    def __init__(self, channels, reduction=8):
        super(Squeeze_Conv, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv1 = nn.Conv2d(channels, channels//reduction, kernel_size=1, padding=0)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(channels//reduction, channels, kernel_size=1, padding=0)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out = self.avg_pool(x)
        out = self.conv1(out)
        out = self.relu(out)
        out = self.conv2(out)
        weight = self.sigmoid(out)

        return weight

def autopad_mfcm(k, p=None, d=1):  # kernel, padding, dilation
    """Pad to 'same' shape outputs."""
    if d > 1:
        k = d * (k - 1) + 1 if isinstance(k, int) else [d * (x - 1) + 1 for x in k]  # actual kernel-size
    if p is None:
        p = k // 2 if isinstance(k, int) else [x // 2 for x in k]  # auto-pad
    return p

class Conv_act(nn.Module):
    """Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)."""

    default_act = nn.SiLU()  # default activation

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        """Initialize Conv layer with given arguments including activation."""
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad_mfcm(k, p, d), groups=g, dilation=d, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x):
        """Apply convolution, batch normalization and activation to input tensor."""
        return self.act(self.bn(self.conv(x)))

    def forward_fuse(self, x):
        """Perform transposed convolution of 2D data."""
        return self.act(self.conv(x))

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
        self.qkv = Conv_act(dim, h, 1)
        self.proj = Conv_act(dim, dim, 1)
        self.pe = Conv_act(dim, dim, 3, 1)

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

class SPP(nn.Module):
    """Spatial Pyramid Pooling (SPP) layer https://arxiv.org/abs/1406.4729."""

    def __init__(self, c1, c2, k=(5, 9, 13)):
        """Initialize the SPP layer with input/output channels and pooling kernel sizes."""
        super().__init__()
        c_ = c1 // 2  # hidden channels
        self.cv1 = Conv_act(c1, c_, 1, 1)
        self.cv2 = Conv_act(c_ * (len(k) + 1), c2, 1, 1)
        self.m = nn.ModuleList([nn.MaxPool2d(kernel_size=x, stride=1, padding=x // 2) for x in k])

    def forward(self, x):
        """Forward pass of the SPP layer, performing spatial pyramid pooling."""
        x = self.cv1(x)
        return self.cv2(torch.cat([x] + [m(x) for m in self.m], 1))

class Bottleneck_(nn.Module):
    """Standard bottleneck."""

    def __init__(self, c1, c2, shortcut=True, g=1, k=(3, 3), e=0.5):
        """Initializes a bottleneck module with given input/output channels, shortcut option, group, kernels, and
        expansion.
        """
        super().__init__()
        c_ = int(c2 * e)  # hidden channels
        self.cv1 = Conv_act(c1, c_, k[0], 1)
        self.cv2 = Conv_act(c_, c2, k[1], 1, g=g)
        self.add = shortcut and c1 == c2

    def forward(self, x):
        """'forward()' applies the YOLO FPN to input data."""
        return x + self.cv2(self.cv1(x)) if self.add else self.cv2(self.cv1(x))

class Conv1_1(nn.Module):
    """Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)."""

    def __init__(self, in_channels, out_channels, kernel_size):
        """Initialize Conv layer with given arguments including activation."""
        super().__init__()
        self.conv = nn.Conv2d(in_channels, in_channels, 1)

    def forward(self, x):
        return self.conv(x)

class Conv1_2(nn.Module):
    """Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)."""

    def __init__(self, in_channels, out_channels, kernel_size):
        """Initialize Conv layer with given arguments including activation."""
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 1)

    def forward(self, x):
        return self.conv(x)

class MFCM(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        #assert (in_ch == out_ch)

        self.c = int(in_ch * 0.25)

        self.conv1 = Conv1_2(in_ch, in_ch, 1)
        self.conv2 = Conv1_2(self.c, 2*self.c, 1)

        self.se = Squeeze_Conv(self.c)
        self.msha = MSHA(self.c)
        self.spp = SPP(self.c, self.c)

    def forward(self, x):
        b, c, _, _ = x.size()
        #print(f"{x.shape}, {c}")
        x = self.conv1(x)
        # print(f"{x.shape}")
        # exit()
        a, b, c, d = x.split((self.c, self.c, self.c, self.c), dim=1)


        a = self.se(a)*a
        a = self.conv2(a)

        b = self.msha(b)
        b = self.conv2(b)

        c = self.spp(c)
        c = self.conv2(c)

        d = self.conv2(d)

        x1 = a+b
        y1 = c+d

        # print(f"{x1.shape}, {y1.shape}")
        # exit()

        output = torch.cat((x1, y1), dim=1)
        #print(f"{output.shape}")
        return output

class CRC(nn.Module):
    def __init__(self, channel, reduction=16):
        super(CRC, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)  # Global average pooling
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)  # Recalibrate the channels

class CRMSFF_2(nn.Module):
    def __init__(self, channel1, channel2, stride=1, scale=0.1, dimension=1):
        super().__init__()
        #assert (in_ch == out_ch)

        self.d = dimension
        self.Channel1 = channel1
        self.Channel2 = channel2
        self.Channel_all = channel1 + channel2
        self.w = CRC(self.Channel_all)
        self.epsilon = 1e-4

        self.c = int(self.Channel_all * 0.25)

        self.conv1 = Conv1_1(self.Channel_all, self.Channel_all, 1)
        self.conv2 = Conv1_2(self.c, 2*self.c, 1)

        self.se = Squeeze_Conv(self.c)
        self.bottleneck = Bottleneck_(self.c, self.c)
        self.msha = MSHA(self.c)
        self.spp = SPP(self.c, self.c)

    def forward(self, x):
        #print(f'input x0 {x[0].shape}, input x1 {x[1].shape}')
        N1, C1, H1, W1 = x[0].size()
        N2, C2, H2, W2 = x[1].size()

        if C1 != self.Channel1 or C2 != self.Channel2:
            raise ValueError(f"Expected input channels: {self.Channel1}, {self.Channel2}, but got {C1}, {C2}.")

        x = torch.cat((x[0], x[1]), dim=1)

        x = self.w(x)       #经过CRC  通道再矫正卷积
        #b, c, _, _ = x.size()
        #print(f"{x.shape}, {c}")
        x = self.conv1(x)
        # print(f"{x.shape}")
        # exit()
        a, b, c, d = x.split((self.c, self.c, self.c, self.c), dim=1)


        a = self.se(a)*a
        b = self.bottleneck(b)
        x1 = a+b

        c = self.spp(c)
        y1 = c+d

        x1 = self.conv2(x1)
        y1 = self.conv2(y1)

        # print(f"{x1.shape}, {y1.shape}")
        # exit()

        output = torch.cat((x1, y1), dim=1)
        #print(f"CRMSFF output: {output.shape}")
        return output

class CRMSFF_3(nn.Module):
    def __init__(self, channel1, channel2, channel3, stride=1, scale=0.1, dimension=1):
        super().__init__()
        #assert (in_ch == out_ch)

        self.d = dimension
        self.Channel1 = channel1
        self.Channel2 = channel2
        self.Channel3 = channel3
        self.Channel_all = int(channel1 + channel2 + channel3)
        self.w = CRC(self.Channel_all)
        self.epsilon = 1e-4

        self.c = int(self.Channel_all * 0.25)

        self.conv1 = Conv1_2(self.Channel_all, self.Channel_all, 1)
        self.conv2 = Conv1_2(self.c, 2*self.c, 1)

        self.se = Squeeze_Conv(self.c)
        self.bottleneck = Bottleneck_(self.c, self.c)
        self.msha = MSHA(self.c)
        self.spp = SPP(self.c, self.c)

    def forward(self, x):
        N1, C1, H1, W1 = x[0].size()
        N2, C2, H2, W2 = x[1].size()
        N3, C3, H3, W3 = x[2].size()

        if C1 != self.Channel1 or C2 != self.Channel2 or C3 != self.Channel3:
            raise ValueError(
                f"Expected input channels: {self.Channel1}, {self.Channel2}, {self.Channel3}, but got {C1}, {C2}, {C3}.")

        if not (H1 == H2 == H3 and W1 == W2 == W3):
            raise ValueError("All inputs must have the same spatial dimensions.")

        x = torch.cat((x[0], x[1], x[2]), dim=1)

        x = self.w(x)       #经过CRC  通道再矫正卷积
        #b, c, _, _ = x.size()
        #print(f"{x.shape}, {c}")
        x = self.conv1(x)
        # print(f"{x.shape}")
        # exit()
        a, b, c, d = x.split((self.c, self.c, self.c, self.c), dim=1)

        a = self.se(a) * a
        b = self.bottleneck(b)
        x1 = a + b

        c = self.spp(c)
        y1 = c + d

        x1 = self.conv2(x1)
        y1 = self.conv2(y1)

        # print(f"{x1.shape}, {y1.shape}")
        # exit()

        output = torch.cat((x1, y1), dim=1)
        # print(f"{output.shape}")
        #print(output)
        return output



