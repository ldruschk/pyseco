from threading import Event, Thread
from queue import Queue


class pyseco_plugin():
    def __init__(self, pyseco, db=False):
        self.pyseco = pyseco
        self.event = Event()
        self.callback_queue = Queue()
        self.db_required = db
        self.db = None
        self.stop_event = Event()
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
        self.console_log("plugin started")

    def run(self):
        if self.db_required:
            try:
                self.db = self.pyseco.connect_db()
            except Exception as e:
                self.error_log("failed to connect to DB: %s" % str(e),
                               fatal=True)
                return
        while not self.stop_event.is_set():
            self.callback_wait()
        self.shutdown()

    def shutdown(self):
        if self.db is not None:
            self.db.close()
        self.console_log("plugin shutting down")

    def callback_wait(self):
        while not self.callback_queue:
            self.event.wait()
            self.event.clear()
            if self.stop_event.is_set():
                return

        self.process_callback(self.callback_queue.get())

    def callback_notify(self, value):
        self.callback_queue.put(value)
        self.event.set()

    def stop(self):
        self.stop_event.set()
        self.event.set()

    def process_callback(self, value):
        raise NotImplementedError()

    def console_log(self, string):
        self.pyseco.console_log("[%s] %s" % (self.__class__.__name__, string))

    def error_log(self, string, fatal=False):
        self.pyseco.error_log("[%s] %s" % (self.__class__.__name__, string))
        if fatal:
            self.stop()
