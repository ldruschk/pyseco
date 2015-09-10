from threading import Event, Thread
from queue import Queue


class pyseco_plugin():
    def __init__(self, pyseco, db=False):
        self.pyseco = pyseco
        self.event = Event()
        self.callback_queue = Queue()
        self.chat_command_queue = Queue()
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
        while self.callback_queue.empty() and self.chat_command_queue.empty():
            self.event.wait()
            self.event.clear()
            if self.stop_event.is_set():
                return

        while not self.callback_queue.empty():
            self.process_callback(self.callback_queue.get())
        while not self.chat_command_queue.empty():
            self.process_chat_command(*self.chat_command_queue.get())

    def callback_notify(self, value):
        self.callback_queue.put(value)
        self.event.set()

    def chat_command_notify(self, command, params, login, admin, mod):
        self.chat_command_queue.put((command, params, login, admin, mod))
        self.event.set()

    def stop(self):
        self.stop_event.set()
        self.event.set()

    def process_callback(self, value):
        raise NotImplementedError()

    def process_chat_command(self, command, params, login, admin, op):
        raise NotImplementedError()

    def register_chat_command(self, command):
        self.pyseco.register_chat_command(command, self)

    def register_callback(self, value):
        self.pyseco.add_callback_listener(value, self)

    def console_log(self, string):
        self.pyseco.console_log("[%s] %s" % (self.__class__.__name__, string))

    def error_log(self, string, fatal=False):
        self.pyseco.error_log("[%s] %s" % (self.__class__.__name__, string))
        if fatal:
            self.stop()
