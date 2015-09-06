from threading import Event, Thread
from queue import Queue

class pyseco_plugin():
    def __init__(self, pyseco):
        self.pyseco = pyseco
        self.event = Event()
        self.callback_queue = Queue()
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while True:
            while not self.callback_queue:
                self.event.wait()
                self.event.clear()

            self.process_callback(self.callback_queue.get())

    def callback_notify(self, value):
        self.callback_queue.put(value)
        self.event.set()
