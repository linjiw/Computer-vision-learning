# CMU 16-726 Learning-Based Image Synthesis / Spring 2023, Assignment 3
# The code base is based on the great work from CSC 321, U Toronto
# https://www.cs.toronto.edu/~rgrosse/courses/csc321_2018/assignments/a4-code.zip
# CSC 321, Assignment 4
#
# This file contains the models used for both parts of the assignment:
#
#   - DCGenerator        --> Used in the vanilla GAN in Part 1
#   - CycleGenerator     --> Used in the CycleGAN in Part 2
#   - DCDiscriminator    --> Used in both the vanilla GAN in Part 1
#   - PatchDiscriminator --> Used in the CycleGAN in Part 2
# For the assignment, you are asked to create the architectures of these
# three networks by filling in the __init__ and forward methods in the
# DCGenerator, CycleGenerator, DCDiscriminator, and PatchDiscriminator classes.
# Feel free to add and try your own models

import torch
import torch.nn as nn


def up_conv(in_channels, out_channels, kernel_size, stride=1, padding=1,
            scale_factor=2, norm='batch', activ=None):
    """Create a transposed-convolutional layer, with optional normalization."""
    layers = []
    layers.append(nn.Upsample(scale_factor=scale_factor, mode='nearest'))
    layers.append(nn.Conv2d(
        in_channels, out_channels,
        kernel_size, stride, padding, bias=norm is None
    ))
    if norm == 'batch':
        layers.append(nn.BatchNorm2d(out_channels))
    elif norm == 'instance':
        layers.append(nn.InstanceNorm2d(out_channels))

    if activ == 'relu':
        layers.append(nn.ReLU())
    elif activ == 'leaky':
        layers.append(nn.LeakyReLU())
    elif activ == 'tanh':
        layers.append(nn.Tanh())

    return nn.Sequential(*layers)


def conv(in_channels, out_channels, kernel_size, stride=2, padding=1,
         norm='batch', init_zero_weights=False, activ=None):
    """Create a convolutional layer, with optional normalization."""
    layers = []
    conv_layer = nn.Conv2d(
        in_channels=in_channels, out_channels=out_channels,
        kernel_size=kernel_size, stride=stride, padding=padding,
        bias=norm is None
    )
    if init_zero_weights:
        conv_layer.weight.data = 0.001 * torch.randn(
            out_channels, in_channels, kernel_size, kernel_size
        )
    layers.append(conv_layer)

    if norm == 'batch':
        layers.append(nn.BatchNorm2d(out_channels))
    elif norm == 'instance':
        layers.append(nn.InstanceNorm2d(out_channels))

    if activ == 'relu':
        layers.append(nn.ReLU())
    elif activ == 'leaky':
        layers.append(nn.LeakyReLU())
    elif activ == 'tanh':
        layers.append(nn.Tanh())
    return nn.Sequential(*layers)


class DCGenerator(nn.Module):

    def __init__(self, noise_size, conv_dim=64):
        super().__init__()

        ###########################################
        ##   FILL THIS IN: CREATE ARCHITECTURE   ##
        ###########################################

        self.up_conv1 = conv(100, 256, 2, 1, 2, 'instance', False,'relu' )
        self.up_conv2 = up_conv(256, 128, 3, stride=1, padding=1, scale_factor=2, norm='instance', activ='relu')
        self.up_conv3 = up_conv(128, 64, 3, stride=1, padding=1, scale_factor=2, norm='instance', activ='relu')
        self.up_conv4 = up_conv(64, 32, 3, stride=1, padding=1, scale_factor=2, norm='instance', activ='relu')
        self.up_conv5 = up_conv(32, 3, 3, stride=1, padding=1, scale_factor=2, norm= None, activ='tanh')

    def forward(self, z):
        """
        Generate an image given a sample of random noise.

        Input
        -----
            z: BS x noise_size x 1 x 1   -->  16x100x1x1

        Output
        ------
            out: BS x channels x image_width x image_height  -->  16x3x64x64
        """
        ###########################################
        ##   FILL THIS IN: FORWARD PASS   ##
        ###########################################
        z = self.up_conv1(z)
        z = self.up_conv2(z)
        z = self.up_conv3(z)
        z = self.up_conv4(z)
        z = self.up_conv5(z)
        return z
        pass


class ResnetBlock(nn.Module):

    def __init__(self, conv_dim, norm, activ):
        super().__init__()
        self.conv_layer = conv(
            in_channels=conv_dim, out_channels=conv_dim,
            kernel_size=3, stride=1, padding=1, norm=norm,
            activ=activ
        )

    def forward(self, x):
        out = x + self.conv_layer(x)
        return out


class CycleGenerator(nn.Module):
    """Architecture of the generator network."""

    def __init__(self, conv_dim=64, init_zero_weights=False, norm='instance'):
        super().__init__()

        ###########################################
        ##   FILL THIS IN: CREATE ARCHITECTURE   ##
        ###########################################

        # # 1. Define the encoder part of the generator
        self.conv1 = conv(3, 32, 4, 2, 1, norm, False, 'relu')
        self.conv2 = conv(32, 64, 4, 2, 1, norm, False, 'relu')

        # # 2. Define the transformation part of the generator
        self.resnet_block = nn.Sequential(ResnetBlock(conv_dim = 64, norm = norm, activ = 'relu'),
                                          ResnetBlock(conv_dim = 64, norm = norm, activ = 'relu'),
                                          ResnetBlock(conv_dim = 64, norm = norm, activ = 'relu'),)

        # # 3. Define the decoder part of the generator
        self.up_conv1 = up_conv(64, 32, 3, stride=1, padding=1, scale_factor=2, norm='instance', activ='relu')
        self.up_conv2 = up_conv(32, 3, 3, stride=1, padding=1, scale_factor=2, norm= None, activ='tanh')

    def forward(self, x):
        """
        Generate an image conditioned on an input image.

        Input
        -----
            x: BS x 3 x 32 x 32

        Output
        ------
            out: BS x 3 x 32 x 32
        """
        ###########################################
        ##   FILL THIS IN: FORWARD PASS   ##
        ###########################################
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.resnet_block(x)
        x = self.up_conv1(x)
        x = self.up_conv2(x)

        return x
        pass


class DCDiscriminator(nn.Module):
    """Architecture of the discriminator network."""

    def __init__(self, conv_dim=64, norm='instance'):
        super().__init__()
        self.conv1 = conv(3, 32, 4, 2, 1, norm, False, 'relu')
        self.conv2 = conv(32, 64, 4, 2, 1, norm, False, 'relu')
        self.conv3 = conv(64, 128, 4, 2, 1, norm, False, 'relu')
        self.conv4 = conv(128, 256, 4, 2, 1, norm, False, 'relu')
        self.conv5 = conv(256, 1, 4, 2, 0, None, False)

    def forward(self, x):
        """Forward pass, x is (B, C, H, W)."""
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x.squeeze()


class PatchDiscriminator(nn.Module):
    """Architecture of the patch discriminator network."""

    def __init__(self, conv_dim=64, norm='batch'):
        super().__init__()

        ###########################################
        ##   FILL THIS IN: CREATE ARCHITECTURE   ##
        ###########################################

        # Hint: it should look really similar to DCDiscriminator.
        self.conv1 = conv(3, 32, 4, 2, 1, norm, False, 'relu')
        self.conv2 = conv(32, 64, 4, 2, 1, norm, False, 'relu')
        self.conv3 = conv(64, 128, 4, 2, 1, norm, False, 'relu')
        self.conv4 = conv(128, 256, 4, 2, 1, norm, False, 'relu')
        self.conv5 = conv(256, 1, 3, 1, 1, None, False)


    def forward(self, x):

        ###########################################
        ##   FILL THIS IN: FORWARD PASS   ##
        ###########################################
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x
        pass


if __name__ == "__main__":
    a = torch.rand(4, 3, 64, 64)
    D = PatchDiscriminator()
    print(D(a).shape)
    G = CycleGenerator()
    print(G(a).shape)