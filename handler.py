class Handler:
    def __init__(self):
        self._users = []
        self._videos = []
        self._online_users = []
        self._delimieter = '\t\n'

    def process(self, command):
        response = ''

        splits = command.split(self._delimiter)
        validation = self._validate(splits)

        if validation == 'OK':
            pass
        else:
            response = f'Error: {validation}'

        return response

    def _validate(self, splits):
        pass

    def _login_user(self, username, password):
        pass

    def _register_user(self, username, password, type):
        pass

    def _add_comment(self, video_id, content):
        pass

    def _add_like(self, video_id, type):
        pass

    def _upload_video(self, video_name, content):
        pass

    def _show_video(self, video_id):
        pass

    def _restrict_vidoe(self, video_id):
        pass

    def _block_video(self, video_id):
        pass

    def _unstrike_user(self, username):
        pass

    def _accept_admin(self, username):
        pass
