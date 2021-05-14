#%%
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt

class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for sub-classes of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()


#%% open stream
CHANNELS = 1
RATE = 44100
sd.default.samplerate = RATE
sd.default.channels = CHANNELS

CHUNK = 2048 # RATE / number of updates per second
fftTime = np.fft.rfftfreq(CHUNK, 1/RATE)


# use a Blackman window
window = np.blackman(CHUNK)

x = 0

#%%
main_indata=None
def set_main_indata(indata: np.ndarray, frames: int, t, status: sd.CallbackFlags):
    global main_indata
    main_indata=indata

def resetAxes():
    ax1.cla()
    ax1.axis('off')
    ax1.axis([0, CHUNK-1, -1, 1])
    # ax1.grid()
    # ax1.set_title('Wave')

    ax2.cla()
    ax2.axis('off')
    ax2.set_yscale('log')
    ax2.set_xscale('log')
    ax2.axis([10, fftTime[-1], 1e-7, 1e5])
    # ax2.grid()
    # ax2.set_title('Frequency Spectrum')

def soundPlot(data):
    if data is None:
        return
    # t1=time.time()
    windowed_data = data[:, 0] * window
    fftData=np.abs(np.fft.rfft(windowed_data))

    # redraw just the points
    #Plot time domain
    lnWave.set_ydata(windowed_data)
    #Plot frequency domain graph
    lnFreq.set_data(fftTime, fftData)
    # tell the blitting manager to do its thing
    bm.update()

    # print("took %.02f ms"%((time.time()-t1)*1000))
    # # use quadratic interpolation around the max
    # which = fftData[1:].argmax() + 1
    # if which != len(fftData)-1:
    #     y0,y1,y2 = np.log(fftData[which-1:which+2:])
    #     x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
    #     # find the frequency and output it
    #     thefreq = (which+x1)*RATE/CHUNK
    #     print("The freq is %f Hz." % (thefreq))
    # else:
    #     thefreq = which*RATE/CHUNK
    #     print("The freq is %f Hz." % (thefreq))

# import queue
# callback_queue = queue.Queue()

# def runOnMainThread(fun):
#     callback_queue.put(fun)

# def from_main_thread_blocking():
#     callback = callback_queue.get() #blocks until an item is available
#     callback()

# def from_main_thread_nonblocking():
#     while True:
#         try:
#             callback = callback_queue.get(False) #doesn't block
#             callback()
#             return True
#         except queue.Empty: #raised when queue is empty
#             return False

if __name__=="__main__":
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, figsize=(10,4))
    resetAxes()
    lnWave, = ax1.plot(np.zeros(CHUNK), animated=True)
    lnFreq, = ax2.plot(fftTime, np.zeros_like(fftTime), animated=True)
    bm = BlitManager(fig.canvas, [lnWave, lnFreq])
    fig.canvas.draw()
    with sd.InputStream(blocksize=CHUNK, callback=set_main_indata):
        while True:
            # time.sleep(.02)
            soundPlot(main_indata)
            # response = input()
            # if response in ('', 'q', 'Q'):
            #     break
            # for ch in response:
            #     if ch == '+':
            #         args.gain *= 2
            #     elif ch == '-':
            #         args.gain /= 2
            #     else:
            #         print('\x1b[31;40m', usage_line.center(args.columns, '#'),
            #               '\x1b[0m', sep='')
            #         break