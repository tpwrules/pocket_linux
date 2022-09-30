from migen import *

from litex.soc.cores.video import video_data_layout
from litex.soc.interconnect import stream

from litex.build.io import SDROutput, DDROutput

class VideoPocketPHY(Module):
    def __init__(self, pads, clock_domain="sys"):
        self.sink = sink = stream.Endpoint(video_data_layout)

        # # #

        # Always ack Sink, no backpressure.
        self.comb += sink.ready.eq(1)

        # Drive Clk.
        self.specials += DDROutput(i1=1, i2=0, o=pads.clk, clk=ClockSignal(clock_domain+"_90"))

        # Drive Controls.
        self.specials += SDROutput(i=sink.de, o=pads.de, clk=ClockSignal(clock_domain))
        self.specials += SDROutput(i=sink.hsync,  o=pads.hsync,   clk=ClockSignal(clock_domain))
        self.specials += SDROutput(i=sink.vsync,  o=pads.vsync,   clk=ClockSignal(clock_domain))
        out = Signal()
        self.comb += out.eq(0)
        self.specials += SDROutput(i=out, o=pads.skip, clk=ClockSignal(clock_domain))

        # Drive Datas.
        data = Signal(24)
        for i in range(8):
            self.comb += data[0+i].eq(sink.b[i] & sink.de)
            self.comb += data[8+i].eq(sink.g[i] & sink.de)
            self.comb += data[16+i].eq(sink.r[i] & sink.de)

        for i in range(12):
            self.specials += DDROutput(i1=data[i+12], i2=data[i], o=pads.data[i], clk=ClockSignal(clock_domain))
