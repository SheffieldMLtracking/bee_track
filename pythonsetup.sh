#!/bin/bash

python -m venv bee-venv

bee-venv/bin/pip install ninja
bee-venv/bin/pip install git+https://github.com/lionfish0/bee_track.git

git clone https://github.com/lionfish0/bee_track.git to_run

bee-venv/bin/pip install PyGObject rpimotorlib rpi-lgpio psutil spidev requests
bee-venv/bin/pip install psutil
bee-venv/bin/pip install scipy libsvm mem_top flask_compress
bee-venv/bin/pip install -U flask-cors

git clone https://github.com/lionfish0/retrodetect.git
bee-venv/bin/pip install -e retrodetect/.
git clone https://github.com/lionfish0/QueueBuffer.git
bee-venv/bin/pip install -e QueueBuffer/.

echo "Python setup complete"
echo "Now run aravissetup as super user in root"
echo "sudo sh bee_track/aravissetup"