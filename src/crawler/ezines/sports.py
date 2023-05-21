import os
import sys

# IMPORTANT! first, call `configure()` to initialize the newsutils lib
# this requires availing the path to the `crawler` module to `configure()`, ie. './src'
from newsutils.conf import configure
sys.path.append(os.getcwd())
configure()


# fetch sports news script
from newsutils.ezines import Sports
if __name__ == '__main__':

    # fetch all sport events
    sports = Sports()
    sports.save_all()

