from plugins.pyseco_plugin import pyseco_plugin


class admin(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.register_chat_command("admin")

    def process_chat_command(self, command, params, login, admin, op):
        if command == "admin":
            if len(params) > 0 and admin:
                self.handle_admin(params)

    def handle_admin(self, params):
        cmd = params[0]
        options = params[1:]
        opt_count = len(options)

        if cmd == "SetTimeAttackLimit" and opt_count == 1:
            self.pyseco.query((int(options[0]), ), "SetTimeAttackLimit")
