# File has been converted to Python3 from Python2 using 2to3 tool

import logging

logger = logging.getLogger('pqa_logger')
logger.setLevel(logging.DEBUG)


class Mib:
    @property
    def is_set(self):
        return "s" in self.type

    @property
    def is_get(self):
        return "g" in self.type

    def __init__(self, mib_string):
        # 0s1234 c4.sy.sub "ethernet"
        self.error = False
        self.type = None
        self.packet_number = None
        self.command = None

        self.param = []
        try:
            t_mib_string = mib_string.strip()
            split_ = t_mib_string.split(" ")
            # ['0g1234', 'c4.dmx.led', '01', '02', '03']
            # print str(split_)
            # logger.debug(split_)

            self.type = split_[0][1:2]

            # print(str(split_[0][2:]))
            self.packet_number = int(split_[0][2:], 16)
            self.command = split_[1]
            for item in split_[2:]:
                self.param.append(item)

            self.raw = mib_string
        except Exception as e:
            # traceback.print_exc()
            logger.error(e, exc_info=True)
            self.error = True
            mib_string = ""
            self.raw = mib_string

    def __str__(self):
        return self.raw


if __name__ == "__main__":
    mib = Mib("test")
    mib = Mib("0g1234 c4.pqa.relays 01 02")
    print(str(mib))
