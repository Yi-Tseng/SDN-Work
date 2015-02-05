from threading import Thread
from time import sleep

class StaticUpdater(Thread):
    """docstring for StaticUpdater"""
    def __init__(self):
        super(StaticUpdater, self).__init__()
        self.ryu_app = None
        self.daemon = True

    def set_ryu_app(self, app):
        self.ryu_app = app

    def run(self):

        print "Starting updater"
        sleep(5)
        print "Started"

        while True:

            if self.ryu_app != None:
                dps = self.ryu_app.dps

                for dp in dps:
                    parser = dp.ofproto_parser
                    ofproto = dp.ofproto
                    msg = parser.OFPPortStatsRequest(dp, 0, ofproto.OFPP_ANY)
                    "Msg sent"
                    dp.send_msg(msg)

            sleep(1)
