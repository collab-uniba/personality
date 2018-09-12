import regex

REX_EMAIL = regex.compile(
    r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?")


class Alias:
    def __init__(self,
                 uid=None,
                 login=None,
                 name=None,
                 email=None,
                 record_type=None,
                 continent=None
                 ):

        self.uid = uid
        self.login = login.strip()
        self.name = name.strip()
        self.record_type = record_type
        self.continent = continent
        self.email, self.email_prefix, self.email_domain = self.parse_email(email)

    @staticmethod
    def parse_email(email):
        email = email.strip().lower()
        if email == 'none' or not len(email):
            email = None
        if email is not None:
            me = REX_EMAIL.search(email)
            if me is None:
                if email.endswith('.(none)'):  # FIXME why not
                    # http://stackoverflow.com/a/897611/1285620
                    email = None
        if email is not None:
            if email == '' or \
                    email.endswith('@server.fake') or \
                    email.endswith('@server.com') or \
                    email.endswith('@example.com') or \
                    email.startswith('dev@') or \
                    email.startswith('user@') or \
                    email.startswith('users@') or \
                    email.startswith('noreply@') or \
                    email.startswith('no-reply@') or \
                    email.startswith('private@') or \
                    email.startswith('announce@') or \
                    email.endswith('@email.com'):
                email = None

        prefix = None
        domain = None
        if email is not None:
            email_parts = email.split('@')
            if len(email_parts) > 1:
                prefix = email_parts[0]
                if not len(prefix):
                    prefix = None
                domain = email_parts[-1]
                if not len(domain):
                    domain = None

        return email, prefix, domain
