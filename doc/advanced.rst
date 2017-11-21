.. _advanced usage:

Advanced Usage
==============

.. index::
    single: phishing

.. _phishing:

Avoiding Phishing Attacks
-------------------------

Phishing is a very common method used on the web to get people to
unknowingly divulge sensitive information such as account
credentials.  It is generally accomplished by sending misleading
URLs in email or placing them on websites. When you visit these
URLs you are taken to a site that looks identical to the site you
were expecting to go to in the hope that you are tricked into giving
up your account credentials.  It used to be that if you carefully
inspected the url you could spot deception, but even that is no
longer true.

Avendesora helps you avoid phishing attacks in two ways. First, you
should never go to one of your secure sites by clicking on a link.
Instead, you should use Avendesora's :ref:`browse command <browse command>`::

    avendesora browse chase

In this way you use the URL stored in Avendesora rather than
trusting a url link provided by a third party. Second, you should
auto-type the account credentials using Avendesora's account
discovery based on RecognizeURL() (be sure to use RecognizeURL() for
websites rather than RecognizeTitle() when configuring account
discovery). RecogniseURL() will not be fooled by a phishing site).


.. index::
    single: discovery
    single: account discovery

.. _discovery:

Account Discovery
-----------------

If you do not give an account to 'avendesora value', Avendesora will
try to determine the account by simply asking each account. An
account can look at the window title, the user name, the host name,
the working directory, and the environment variables to determine if
it is suitable. If so, it nominates itself. If there is only one
account nominated, that account is used. If there are multiple
nominees, then a small window pops up allowing you to choose
which account you wish to use.

.. index::
    single: RecognizeTitle

To configure an account to trigger when a particular window title is
seen, use:

.. code-block:: python

    discovery = RecognizeTitle(
        'Chase Online *',
        script='{username}{tab}{passcode}{return}'
    )

The title is a glob string, meaning that '*' matches any combination
of characters. The script describes what Avendesora should output
when their is a match. In this case it outputs the username field,
then a tab, then the passcode field, then a return (see 'avendesora
help scripts').

Matching window titles can be fragile, especially for websites
because the titles can vary quite a bit across the site and over
time. To accommodate this variation, you can give multiple glob
patterns:

.. code-block:: python

    discovery = RecognizeTitle(
        'CHASE Bank*',
        'Chase Online*',
        script='{username}{tab}{passcode}{return}'
    )

.. index::
    single: RecognizeURL

If you use Firefox, you can install the 'Add URL to Window Title'
extension.  It is a plugin that makes discovery easier and more
robust by adding the URL to the title.  For Chrome the appropriate
plugin is  is 'URL in Title'.  It is recommended that you install
the appropriate one into your browser.  For AddURLToWindowTitle, set
the following options:

.. code-block:: python

    show full URL = yes
    separator string = '-'
    show field attributes = no

For URLinTitle, set::

    tab title format = '{title} - {protocol}://{hostname}{port}/{path}'

RecognizeURL designed to recognize such titles. Once you have
deployed the appropriate plugin, you can use:

.. code-block:: python

    discovery = RecognizeURL(
        'https://chaseonline.chase.com',
        'https://www.chase.com',
        script='{username}{tab}{passcode}{return}'
    )

When giving the URL, anything specified must match and globbing is
not supported. If you give a partial path, by default Avendesora
will match up to what you have given, but you can require an exact
match of the entire path by specifying exact_path=True to
RecognizeURL.  If you do not give the protocol, the default_protocol
(https) is assumed.

In general you should use RecognizeURL() rather than
RecognizeTitle() for websites if you can. Doing so will help protect
you from phishing attacks by carefully examining the URL.

When account discovery fails it can be difficult to determine what
is going wrong. When this occurs, you should first examine the log
file. It should show you the window title and the recognized title
components. You should first assure the title is as expected. If Add
URL to Window Title generated the title, then the various title
components should also be shown.  Then run Avendesora as follows::

    avendesora value --verbose --title '<title>'

The title should be copied from the log file. The verbose option
causes the result of each test to be included in the log file, so
you can determine which recognizer is failing to trigger.  You can
either specify the verbose option on the command line or in the
config file.

The following recognizers are available::

    RecognizeAll(<recognizer>..., [script=<script>])
    RecognizeAny(<recognizer>..., [script=<script>])
    RecognizeTitle(<title>..., [script=<script>])
    RecognizeURL(<title>..., [script=<script>, [name=<name>,]] [exact_path=<bool>])
    RecognizeHost(<host>..., [script=<script>])
    RecognizeUser(<user>..., [script=<script>])
    RecognizeCWD(<cwd>..., [script=<script>])
    RecognizeEnvVar(<name>, <value>, [script=<script>])
    RecognizeNetwork(<mac>..., [script=<script>])
    RecognizeFile(<path>, [<contents>,] [<ttl>,] [script=<script>])

.. index::
    single: RecognizeAll
    single: RecognizeAny

RecognizeAll() and RecognizeAny() can be used to combine several
recognizers. For example:

.. code-block:: python

    discovery = RecognizeAll(
        RecognizeTitle('sudo *'),
        RecognizeUser('hhyde'),
        script='{passcode}{return}'
    )

If the recognizers are given in an array, all are tried, and each
that match are offered. For example:

.. code-block:: python

    discovery = [
        RecognizeURL(
            'http://www.querty-forum.org',
            script='admin{tab}{passcode}{return}',
            name='admin',
        ),
        RecognizeURL(
            'http://www.querty-forum.org',
            script='thecaretaker{tab}{passcode}{return}',
            name='thecaretaker',
        ),
    ]

In this case, both recognizers recognize the same URL, thus they
will both be offered for this site.  But each has a different
script. The name allows the user to distinguish the available
choices.

If there is a need to distinguish URLs where is one is a substring
of another, you can use *exact_path*:

.. code-block:: python

    discovery = [
        RecognizeURL(
            'https://mybank.com/Authentication',
            script='{username}{return}',
            exact_path=True,
        ),
        RecognizeURL(
            'https://mybank.com/Authentication/Password',
            script='{passcode}{return}',
            exact_path=True,
        ),
    ]

.. index::
    single: RecognizeFile

RecognizeFile checks to determine whether a particular file has been
created recently.  This can be use in scripts to force secret
recognition.  For example, the titles used by Firefox and
Thunderbird when collecting the master password is either
non-existent or undistinguished.  These programs also produce a
large amount of uninteresting chatter on their output, so it is
common to write a shell script to run the program that redirects
their output to /dev/null.  Such a script can be modified to
essentially notify Avendesora that a particular password is desired.
For example, for Thunderbird::

    #!/bin/sh
    touch /tmp/thunderbird-1024
    /usr/bin/thunderbird > /dev/null

Here I have adding my user id (uid=1024) to make the filename unique
so I am less likely to clash with other users. Alternately, you
could choose a path that fell within your home directory. Then,
adding:

.. code-block:: python

    class Firefox(Account):
        desc = 'Master password for Firefox and Thunderbird'
        passcode = Password()
        discovery = RecognizeFile(
            '/tmp/thunderbird-1024', wait=60, script='{passcode}{return}'
        )

If the specified file exists and has been updated within the last 60
seconds, then secret is recognized.  You can specify the amount of
time you can wait in between running the script and running
Avendesora with the 'wait' argument, which takes a number of
seconds.  It defaults to 60.

Using this particular approach, every secret would need its own
file. But you can share a file by specifying the file contents.
Then the script could be rewritten as::

    #!/bin/sh
    echo thunderbird > ~/.avendesora-password-request
    /usr/bin/thunderbird > /dev/null

Then you would add something like the following to your accounts file:

.. code-block:: python

    class Firefox(Account):
        desc = 'Master password for Firefox and Thunderbird'
        passcode = Password()
        discovery = RecognizeFile(
            '~/.avendesora-password-request',
            contents='thunderbird',
            script='{passcode}{return}'
        )


.. index::
    single: questions
    single: security questions
    single: chalenge questions

.. _questions:

Security Questions
------------------

Security questions are form of security theater imposed upon you by
many websites. The claim is that these questions increase the
security of your account. In fact they often do the opposite by
creating additional avenues of access to your account. Their real
purpose is to allow you to regain access to your account in case you
lose your password. If you are careful, this is not needed (you do
back up your Avendesora accounts, right?). In this case it is better
to randomly generate your answers.

Security questions are handled by adding something like the
following to your account:

.. code-block:: python

    questions = [
        Question('oldest aunt'),
        Question('title of first job'),
        Question('oldest uncle'),
        Question('savings goal'),
        Question('childhood vacation spot'),
    ]

The string identifying the question does not need to contain the
question verbatim, a abbreviated version is sufficient as long as it
allows you to distinguish the question.  The questions are given as
an array, and so are accessed with an index that starts at 0. Thus,
to get the answer to who is your 'oldest aunt', you would use::

    > avendesora value <accountname> 0
    questions.0 (oldest aunt): ampere reimburse duster

You can get a list of your questions so you can identify which index
to use with::

    > avenedesora values <accountname>
    ...
    questions:
        0: oldest aunt <reveal with 'avendesora value <accountname> questions.0'>
        1: title of first job <reveal with 'avendesora value <accountname> questions.1'>
        2: oldest uncle <reveal with 'avendesora value <accountname> questions.2'>
        3: savings goal <reveal with 'avendesora value <accountname> questions.3'>
        4: childhood vacation spot <reveal with 'avendesora value <accountname> questions.4'>
    ...

By default, Avendesora generates a response that consists of 3
random words. This makes it easy to read to a person over the phone
if asked to confirm your identity.  Occasionally you will not be
able to enter your own answer, but must choose one that is offered
to you. In this case, you can specify the answer as part of the
question:

.. code-block:: python

    questions = [
        Question('favorite fruit', answer='grapes'),
        Question('first major city visited', answer='paris'),
        Question('favorite subject', answer='history'),
    ]

When giving the answers you may want to conceal them to protect them
from casual observation.

Be aware that the question is used as a seed when generating the
answer, so if you change the question in any way it changes the
answer.


.. index::
    single: scripts

.. _scripts:

Scripts
-------

Scripts are strings that contain embedded account attributes.  For
example:

.. code-block:: python

    'username: {username}, password: {passcode}'

When processed by Advendesora the attributes are replaced by their
value from the chosen account.  For example, this script might
be rendered as::

    username: jman, password: R7ibHyPjWtG2

Scripts are useful if you need to combine an account value with
other text, if you need to combine more than one account value, or
if you want quick access to something that would otherwise need an
additional key.

For example, consider an account for your wireless router, which
might hold several passwords, one for administrative access and one
or more for the network passwords.  Such an account might look like:

.. code-block:: python

    class WiFi(Account):
        username = 'admin'
        passcode = Passphrase()
        networks = ["Occam's Router", "Occam's Router (guest)"]
        network_passwords = [Passphrase(), Passphrase()]
        privileged = Script('SSID: {networks.0}, password: {network_passwords.0}')
        guest = Script('SSID: {networks.1}, password: {network_passwords.1}')

Now the credentials for the privileged network are accessed with::

    > avendesora value wifi privileged
    SSID: Occam's Router, password: overdraw cactus devotion saying

Most account attributes that expect a string can also accept a
script given in this manner.

You can also give a script rather than a field on the command line
when running the :ref:`value command <value command>`::

    > avendesora value scc '{username}: {passcode}'
    jman: R7ibHyPjWtG2

It is also possible to specify a script for the value of the
*default* attribute. This attribute allows you to specify the
default field (which attribute name and key to use if one is not
given on the command line).  It also accepts a script rather than a
field, but in this case it should be a simple string and not an
instance of the Script class.  If you passed it as a Script, it
would be expanded before being interpreted as a field name, and so
would result in a 'not found' error.

.. code-block:: python

    class SCC(Acount):
        aliases = 'scc'
        username = 'jman'
        password = PasswordRecipe('12 2u 2d 2s')
        default = 'username: {username}, password: {password}'

You can access the script by simply not providing a field::

    > avendesora value scc
    username: jman, password: *m7Aqj=XBAs7

Finally, you pass a script to the account discovery recognizers.
They specify the action that should be taken when a particular
recognizer triggers. These scripts would also be simple strings and
not instances of the Script class. For example, this recognizer
could be used to recognize Gmail:

.. code-block:: python

    discovery = [
        RecognizeURL(
            'https://accounts.google.com/ServiceLogin',
            script='{username}{return}{sleep 1.5}{passcode}{return}'
        ),
        RecognizeURL(
            'https://accounts.google.com/signin/challenge',
            script='{questions.0}{return}'
        ),
    ]

Besides the account attributes, you can use several other special
attributes including: *{tab}*, *{return}*, and *{sleep N}*.  *{tab}* is
replaced by a tab character, *{return}* is replaced by a carriage
return character, and *{sleep N}* causes a pause of N seconds. The
sleep function is only active when autotyping after account
discovery.


.. index::
    single: stealth accounts

.. _stealth accounts:

Stealth Accounts
----------------

Normally Avendesora uses information from an account that is
contained in an account file to generate the secrets for that
account. In some cases, the presence of the account itself, even
though it is contained within an encrypted file can be problematic.
The mere presence of an encrypted file may result in you being
compelled to open it. For the most damaging secrets, it is best if
there is no evidence that the secret exists at all. This is the
purpose of stealth accounts. (Misdirection is an alternative to
stealth accounts; see 'avendesora help misdirection').

Generally one uses the predefined stealth accounts, which all have
names that are descriptive of the form of the secret they generate,
for example word4 generates a 4-word pass phrase (also referred as
the xkcd pattern)::

    > avendesora value word4
    account: my_secret_account
    gulch sleep scone halibut

The predefined accounts are kept in
~/.config/avendesora/stealth_accounts.  You are free to add new
accounts or modify the existing accounts.

Stealth accounts are subclasses of the StealthAccount class. These
accounts differ from normal accounts in that they do not contribute
the account name to the secrets generators for use as a seed.
Instead, the user is requested to provide the account name every
time the secret is generated. The secret depends strongly
on this account name, so it is essential you give precisely the same
name each time. The term 'account name' is being use here, but you
can enter any text you like.  Best to make this text very difficult
to guess if you are concerned about being compelled to disclose your
GPG keys.

The secret generator will combine the account name with the master
seed before generating the secret. This allows you to use simple
predictable account names and still get an unpredictable secret.
The master seed used is taken from master_seed in the file
that contains the stealth account if it exists, or the user_key if
it does not. By default the stealth accounts file does not contain a
master seed, which makes it difficult to share stealth accounts.
You can create additional stealth account files that do contain
master seeds that you can share with your associates.


.. index::
    single: misdirection

.. _misdirection:

Misdirection
------------

One way to avoid being compelled to disclose a secret is to disavow
any knowledge of the secret.  However, the presence of an account in
Avendesora that pertains to that secret undercuts this argument.
This is the purpose of stealth accounts. They allow you to generate
secrets for accounts for which Avendesora has no stored information.
In this case Avendesora asks you for the minimal amount of
information that it needs to generate the secret. However in some
cases, the amount of information that must be retained is simply too
much to keep in your head. In that case another approach, referred
to as secret misdirection, can be used.

With secret misdirection, you do not disavow any knowledge of the
secret, instead you say your knowledge is out of date. So you would
say something like "I changed the password and then forgot it", or
"The account is closed". To support this ruse, you must use the
--seed (or -S) option to 'avendsora value' when generating your
secret (secrets misdirection only works with generated passwords,
not stored passwords). This causes Avendesora to ask you for an
additional seed at the time you request the secret. If you do not
use --seed or you do and give the wrong seed, you will get a
different value for your secret.  In effect, using --seed when
generating the original value of the secret causes Avendesora to
generate the wrong secret by default, allowing you to say "See, I
told you it would not work". But when you want it to work, you just
interactively provide the correct seed.

You would typically only use misdirection for secrets you are
worried about being compelled to disclose. So it behooves you to use
an unpredictable additional seed for these secrets to reduce the
chance someone could guess it.

Be aware that when you employ misdirection on a secret, the value of
the secret stored in the archive will not be the true value, it
will instead be the misdirected value.


.. index::
    single: collaboration

.. _collaboration:

Collaborating with a Partner
----------------------------

If you share an accounts file with a partner, then either partner
can create new secrets and the other partner can reproduce their
values once a small amount of relatively non-confidential
information is shared. This works because the security of the
generated secrets is based on the master seed, and that seed is
contained in the accounts file that is shared in a secure manner
once at the beginning.  For example, imagine one partner creates an
account at the US Postal Service website and then informs the
partner that the name of the new account is usps and the username is
justus.  That is enough information for the second partner to
generate the password and login. And notice that the necessary
information can be shared over an insecure channel. For example, it
could be sent in a text message or from a phone where trustworthy
encryption is not available.

The first step in using Avendesora to collaborate with a partner is
for one of the partners to generate and then share an accounts file
that is dedicated to the shared accounts.  This file contains the
master seed, and it is critical to keep this value secure. Thus, it
is recommended that the shared file be encrypted.

Consider an example where you, Alice, are sharing accounts with your
business partner, Bob.  You have hired a contractor to run your
email server, Eve, who unbeknownst to you is reading your email in
order to steal valuable secrets.  Together, you and Bob jointly run
Teneya Enterprises. Since you expect more people will need access to
the accounts in the future, you choose to the name the file after
the company rather than your partner.  To share accounts with Bob,
you start by getting Bob's public GPG key.  Then, create the new
accounts file with something like::

    avendesora new -g alice@teneya.com -g bob@teneya.com teneya.gpg

This generates a new accounts file, ~/.config/avendesora/teneya.gpg,
and encrypts it so only you and Bob can open it.  Mail this file to
Bob. Since it is encrypted, it is to safe to send the file through
email.  Even though Eve can read this message, the accounts file is
encrypted so Eve cannot access the master seed it contains.  Bob
should put the file in ~/.config/avendesora and then add it to
accounts_files in ~/.config/avendesora/accounts_files.  You are now
ready to share accounts.

Then, one partner creates a new account and mails the account entry
to the other partner.  This entry does not contain enough
information to allow an eavesdropper such as Eve to be able to
generate the secrets, but now both partners can. At a minimum you
would need to share only the account name and the user name if one
is needed. With that, the other partner can generate the passcode.

Once you have shared an accounts file, you can also use the :ref:`identity
command <identity command>` to prove your identity to your partner.

You cannot share secrets encrypted with Scrypt. Also, you cannot
share stealth accounts unless the file that contains the account
templates has a *master_seed* specified, which they do not by
default. You would need to create a separate file for shared stealth
account templates and add a master seed to that file manually.


.. index::
    single: challenge response
    single: confirming identity

.. _confirming identity:

Confirming Identity of a Partner
--------------------------------

The :ref:`identity command <identity command>` allows you to generate a response 
to any challenge.  The response identifies you to a remote partner with whom you 
have shared an account.

If you run the command with no arguments, it prints the list of
valid names. If you run it with no challenge, one is created for you
based on the current time and date.

If you have a remote partner to whom you wish to prove your
identity, have that partner use avendesora to generate a challenge
and a response based on your shared secret. Then the remote partner
provides you with the challenge and you run avendesora with that
challenge to generate the same response, which you provide to your
remote partner to prove your identity.

You are free to explicitly specify a challenge to start the process,
but it is important that it be unpredictable and that you not use
the same challenge twice. As such, it is recommended that you not
provide the challenge. In this situation, one is generated for you
based on the time and date.

Consider an example that illustrates the process. In this example,
Ahmed is confirming the identity of Reza, where both Ahmed and Reza
are assumed to have shared Avendesora accounts.  Ahmed runs
Avendesora as follows and remembers the response::

    > avendesora identity reza
    challenge: slouch emirate bedeck brooding
    response: spear disable local marigold

This assumes that reza is the name, with any extension removed, of the file that 
Ahmed uses to contain their shared accounts.

Ahmed communicates the challenge to Reza but not the response.  Reza then runs 
Avendesora with the given challenge::

    > avendesora identity ahmed slouch emirate bedeck brooding
    challenge: slouch emirate bedeck brooding
    response: spear disable local marigold

In this example, ahmed is the name of the file that Reza uses to contain their 
shared accounts.

To complete the process, Reza returns the response to Ahmed, who compares it to 
the response he received to confirm Reza's identity.  If Ahmed has forgotten the 
desired response, he can also specify the challenge to the :ref:`identity 
command <identity command>` to regenerate the expected response.


.. index::
    single: phonetic alphabet
    single: alphabet, phonetic

.. _phonetic:

Phonetic Alphabet
-----------------

When on the phone it can be difficult to convey the letters in an account 
identifier or other letter sequences. To help with this *Avendesora* can convert 
the sequence to the NATO phonetic alphabet.  For example, imaging conveying the 
sequence '2WQI1T'. To do so, you can run the following::

    > avendesora phonetic 2WQI1T
    two whiskey quebec india one tango

Alternately, you can run the command without an argument, in which case it 
simply prints out the phonetic alphabet::

    > avendesora p
    Phonetic alphabet:
        Alfa      Echo      India     Mike      Quebec    Uniform   Yankee
        Bravo     Foxtrot   Juliett   November  Romeo     Victor    Zulu
        Charlie   Golf      Kilo      Oscar     Sierra    Whiskey
        Delta     Hotel     Lima      Papa      Tango     X-ray

Now you can easily do the conversion yourself. Having *Avendesora* do the 
conversion for you helps you distinguish similar looking characters such as 
I and 1 and O and 0.


.. index::
    single: abraxas

.. _abraxas:

Upgrading from Abraxas
----------------------

Avendesora generalizes and replaces Abraxas, its predecessor.  To
transition from Abraxas to Avendesora, you will first need to
upgrade Abraxas to version 1.8 or higher (use 'abraxas -v' to
determine version). Then run::

    abraxas --export

It will create a collection of Avendesora accounts files in
~/.config/abraxas/avendesora. You need to manually add these files
to your list of accounts files in Avendesora. Say one such file is
created: ~/.config/abraxas/avendesora/accounts.gpg.  This could be
added to Avendesora as follows:

1. create a symbolic link from
   ~/.config/avendesora/abraxas_accounts.gpg to
   ~/.config/abraxas/avendesora/accounts.gpg::

    cd ~/.config/avendesora
    ln -s ../abraxas/avendesora/accounts.gpg abraxas_accounts.gpg

2. add abraxas_accounts.gpg to account_files list in accounts_files.

Now all of the Abraxas accounts contained in abraxas_accounts.gpg
should be available though Avendesora and the various features of
the account should operate as expected. However, secrets in accounts
exported by Abraxas are no longer generated secrets. Instead, the
actual secrets are placed in a hidden form in the exported accounts
files.

If you would like to enhance the imported accounts to take advantage
of the new features of Avendesora, it is recommended that you do not
manually modify the imported files. Instead, copy the account
information to one of your own account files before modifying it.
To avoid conflict, you must then delete the account from the
imported file. To do so, create ~/.config/abraxas/do-not-export if
it does not exist, then add the account name to this file, and
reexport your accounts from Abraxas.