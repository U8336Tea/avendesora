# Password Generator

# License {{{1
# Copyright (C) 2016-17 Kenneth S. Kundert
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see http://www.gnu.org/licenses/.


# Imports {{{1
from .account import Account
from .config import read_config, get_setting
from .dialog import show_list_dialog
from .gpg import GnuPG, PythonFile, GPG_EXTENSIONS
from .obscure import Hidden
from .preferences import (
    CONFIG_DEFAULTS, NONCONFIG_SETTINGS, ACCOUNTS_FILE_INITIAL_CONTENTS,
    CONFIG_FILE_INITIAL_CONTENTS, CONFIG_DOC_FILE_INITIAL_CONTENTS,
    USER_KEY_FILE_INITIAL_CONTENTS, HASH_FILE_INITIAL_CONTENTS,
    STEALTH_ACCOUNTS_FILE_INITIAL_CONTENTS, ACCOUNT_LIST_FILE_CONTENTS,
)
from .secrets import Passphrase
from .title import Title
from .utilities import generate_random_string, validate_components
from inform import (
    codicil, conjoin, debug, Error, error, notify, log, os_error, render, warn
)
from shlib import to_path, mv, rm
from textwrap import dedent, fill
from pathlib import Path
import os

# PasswordGenerator class{{{1
class PasswordGenerator(object):

    # Constructor {{{2
    def __init__(self, init=False, gpg_ids=None):
        # initialize avendesora (these should already be done if called from 
        # main, but it is safe to call them again)
        read_config()
        GnuPG.initialize()

        # check the integrity of avendesora
        validate_components()

        # create the avendesora data directory
        if init:
            self.initialize(gpg_ids, init)
            return

        # read the accounts files
        self.shared_secrets = {}
        seen = {}
        most_recently_updated = 0
        for filename in get_setting('accounts_files', []):
            path = to_path(get_setting('settings_dir'), filename)
            updated = os.path.getmtime(str(path.resolve()))
            if updated > most_recently_updated:
                most_recently_updated = updated
            account_file = PythonFile(path)
            contents = account_file.run()
            master_seed = contents.get('master_seed')
            if master_seed:
                self.shared_secrets[path.stem] = master_seed

            # traverse through all accounts and pass in fileinfo and master
            # will be ignored if already set
            for account in self.all_accounts():
                account.preprocess(master_seed, account_file, seen)

        # check for missing or stale archive file
        archive_file = get_setting('archive_file')
        if archive_file:
            if archive_file.exists():
                stale = int(get_setting('archive_stale'))
                archive_updated = os.path.getmtime(str(archive_file))
                if most_recently_updated - archive_updated > 86400 * stale:
                    warn('stale archive.')
                    codicil(fill(dedent("""
                        Recommend running 'avendesora changed' to determine
                        which account entries have changed, and if all the
                        changes are expected, running 'avendesora archive' to
                        update the archive.
                    """).strip()))
            else:
                warn('archive missing.')
                codicil(
                    "Recommend running 'avendesora archive'",
                    "to create the archive."
                )

    # initialize() {{{2
    def initialize(self, gpg_ids, filename):
        # If filename is True, this is being called as part of the Avendesora
        # 'initialize' command, in which case all missing files should be created.
        # If filename is a string, this is being called as part of the
        # Avendesora 'new' command, in which case a single new account file
        # should be created.
        def split(s, l=72):
            # Break long string into a series of adjacent shorter strings
            if len(s) < l:
                return '"%s"' % s
            chunks = ['    "%s"' % s[i:i+l] for i in range(0, len(s), l)]
            return '\n' + '\n'.join(chunks) + '\n'

        # Create dictionary of available substitutions for CONTENTS strings
        fields = {}
        for key in CONFIG_DEFAULTS:
            value = get_setting(key, expand=False)
            value = render(str(value) if isinstance(value, Path) else value)
            fields.update({key: value})
        for key in NONCONFIG_SETTINGS:
            value = get_setting(key, expand=False)
            value = render(str(value) if isinstance(value, Path) else value)
            fields.update({key: value})
        fields['encoding'] = get_setting('encoding')
            # get this one again, this time without the quotes
        gpg_ids = gpg_ids if gpg_ids else get_setting('gpg_ids', [])
        fields.update({
            'section': '{''{''{''1',
            'master_seed': split(Hidden.conceal(generate_random_string(72))),
            'user_key': split(Hidden.conceal(generate_random_string(72))),
            'gpg_ids': repr(' '.join(gpg_ids)),
        })

        # delete the config_doc_file so we always get an updated version.
        if (get_setting('config_doc_file')):
            try:
                rm(get_setting('config_doc_file'))
            except OSError as e:
                warn(os_error(e))

        # create the initial versions of the files in the settings directory
        if filename is True:
            path = to_path(get_setting('account_list_file'))
            if path.suffix in GPG_EXTENSIONS:
                raise Error('encryption is not supported.', culprit=path)

            # Assure that the default initial set of files is present
            for path, contents in [
                (get_setting('config_file'), CONFIG_FILE_INITIAL_CONTENTS),
                (get_setting('config_doc_file'), CONFIG_DOC_FILE_INITIAL_CONTENTS),
                (get_setting('hashes_file'), HASH_FILE_INITIAL_CONTENTS),
                (get_setting('user_key_file'), USER_KEY_FILE_INITIAL_CONTENTS),
                (get_setting('default_accounts_file'), ACCOUNTS_FILE_INITIAL_CONTENTS),
                (get_setting('default_stealth_accounts_file'), STEALTH_ACCOUNTS_FILE_INITIAL_CONTENTS),
                (get_setting('account_list_file'), ACCOUNT_LIST_FILE_CONTENTS),
            ]:
                if path:
                    log('creating initial version.', culprit=path)
                    f = PythonFile(path)
                    f.create(contents.format(**fields), gpg_ids)
                        # create will not overwrite an existing file, instead it
                        # reads the file.
        else:
            # Create a new accounts file
            fields['accounts_files'] = render(
                get_setting('accounts_files', []) + [filename]
            )
                # do not sort, the first file is treated special
            path = to_path(get_setting('settings_dir'), filename)
            if path.exists():
                raise Error('exists.', culprit=path)
            if path.suffix in GPG_EXTENSIONS and not gpg_ids:
                raise Error('Must specify GPG IDs.')
            log('creating accounts file.', culprit=path)
            f = PythonFile(path)
            f.create(ACCOUNTS_FILE_INITIAL_CONTENTS.format(**fields), gpg_ids)

            # update the accounts list file
            path = to_path(
                get_setting('settings_dir'), get_setting('account_list_file')
            )
            log('update accounts list.', culprit=path)
            f = PythonFile(path)
            try:
                mv(path, str(path) + '~')
                f.create(ACCOUNT_LIST_FILE_CONTENTS.format(**fields), gpg_ids)
            except OSError as e:
                raise Error(os_error(e))

    # get_account() {{{2
    def get_account(self, name, request_seed=False, stealth_name=None):
        if not name:
            raise Error('no account specified.')
        account = Account.get_account(name)
        account.initialize(request_seed, stealth_name)
        return account

    # discover_account() {{{2
    def discover_account(self, title=None, verbose=False):
        log('Account Discovery ...')

        if not verbose:
            verbose = get_setting('verbose')

        # get and parse the title
        data = Title(override=title).get_data()

        # sweep through accounts to see if any recognize this title data
        matches = {}
        seen = set()
        for account in self.all_accounts():
            name = account.get_name()
            if verbose:
                log('Trying:', name)
            for key, script in account.recognize(data, verbose):
                # identify and skip duplicates
                if (name, script) in seen:
                    continue
                seen.add((name, script))
                ident = '%s (%s)' % (name, key) if key else name
                ident = '%s: %s' % (len(matches), ident)  # assure uniqueness
                matches[ident] = name, script
                log('%s matches' % ident)

        if not matches:
            msg = 'cannot find appropriate account.'
            notify(msg)
            raise Error(msg)
        if len(matches) > 1:
            choice = show_list_dialog('Choose Secret', sorted(matches.keys()))
            if choice:
                log('user selects %s' % choice)
                return matches[choice]
        return matches.popitem()[1]
            # this odd little piece of code returns the value of the one item in
            # the dictionary

    # all_accounts() {{{2
    def all_accounts(self):
        for account in Account.all_accounts():
            yield account

    # find_acounts() {{{2
    def find_accounts(self, target):
        for account in self.all_accounts():
            if account.id_contains(target):
                yield account

    # search_acounts() {{{2
    def search_accounts(self, target):
        for account in self.all_accounts():
            if account.account_contains(target):
                yield account

    # challenge_response() {{{2
    def challenge_response(self, name, challenge):
        """Generate a response to a challenge

        Given the name of a master seed (actually the basename of the file that
        contains the master seed), returns an identifying response to a
        challenge. If no challenge is provided, one is generated based on the
        time and date. Returns both the challenge and the response as a tuple.
        """

        try:
            if not challenge:
                from arrow import utcnow
                now = str(utcnow())
                c = Passphrase()
                c.set_seeds([now])
                challenge = str(c)
            r = Passphrase()
            r.set_seeds([self.shared_secrets[name], challenge])
            response = str(r)
            return challenge, response
        except KeyError:
            choices = conjoin(sorted(self.shared_secrets.keys()))
            raise Error(
                'Unknown partner. Choose from %s.' % choices,
                culprit=name
            )

