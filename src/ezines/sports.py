# configure settings
from newsutils.conf import configure
configure()

from newsutils.requests import Sports


if __name__ == '__main__':


    # fetch all sport events
    sports = Sports()
    sports.save_all()

