# Project Setup

This document provides instructions for setting up the project environment. Follow the steps below to install the required packages and dependencies.

## Requirements

To ensure compatibility and smooth functioning, please install the following packages:

```plaintext
click==8.0.1
colorama==0.4.4
cycler==0.10.0
importlib-metadata==4.6.1
itsdangerous==2.0.1
Jinja2==3.0.1
kiwisolver==1.3.1
MarkupSafe==2.0.1
matplotlib==3.4.2
numpy==1.21.1
opencv-python==4.5.3.56
Pillow==8.3.1
pyparsing==2.4.7
python-dateutil==2.8.2
six==1.16.0
typing-extensions==3.10.0.0
Werkzeug==2.0.1
zipp==3.5.0
scipy==1.13.1
scikit-learn==1.5.0
```
Additionally, for PyTorch and related packages, use the following versions:

```
--find-links https://download.pytorch.org/whl/torch_stable.html
torch==1.7.1+cu110
torchaudio==0.7.2
torchvision==0.8.2+cu110
```
## Installation

1. Create a Virtual Environment (optional but recommended):

```
python -m venv myenv
source myenv/bin/activate  # On Windows, use `myenv\Scripts\activate`
```

2. Install Required Packages:

```
pip install click==8.0.1
pip install colorama==0.4.4
pip install cycler==0.10.0
pip install importlib-metadata==4.6.1
pip install itsdangerous==2.0.1
pip install Jinja2==3.0.1
pip install kiwisolver==1.3.1
pip install MarkupSafe==2.0.1
pip install matplotlib==3.4.2
pip install numpy==1.21.1
pip install opencv-python==4.5.3.56
pip install Pillow==8.3.1
pip install pyparsing==2.4.7
pip install python-dateutil==2.8.2
pip install six==1.16.0
pip install typing-extensions==3.10.0.0
pip install Werkzeug==2.0.1
pip install zipp==3.5.0
pip install scipy==1.13.1
pip install scikit-learn==1.5.0
```

3. Install PyTorch and Related Packages:

```
pip install --find-links https://download.pytorch.org/whl/torch_stable.html torch==1.7.1+cu110
pip install torchaudio==0.7.2
pip install torchvision==0.8.2+cu110
```

Follow these steps to set up your environment. 
If you encounter any issues during installation, 
please refer to the official documentation for each package or reach out for further assistance.
