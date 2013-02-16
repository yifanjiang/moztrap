MozTrap
=======

The upstream Moztrap is located at:

https://github.com/mozilla/moztrap/

This fork aims to provide code for Libreoffice manual test project,
which is distributed and deployed with Libreoffice specific hacks and
features based on a particular upstream branch. The running instance
of Libreoffice Moztrap can be found:

http://manual-test.libreoffice.org/

The fork tries to make the deployment as similar as possible to the
upstream project, though a bit of tuning for
`moztrap/settings/local.py` is required. A working sample of the
settings for a typical development environment is provided in the
following section.


Documentation
-------------

For more information about setting up, developing, and using MozTrap, see the
documentation in the `docs/` directory (or `read it online`_).

To build and view an HTML version of the documentation::

    $ cd docs
    $ pip install sphinx
    $ make html
    $ firefox _build/html/index.html

.. _read it online: http://moztrap.readthedocs.org


Related repositories
--------------------

There are `Selenium`_ tests for MozTrap in the `moztrap-tests`_ repository.

MozTrap's Python dependencies are available as sdist tarballs in the
`moztrap-reqs`_ repository, and as an unpacked vendor library in the
`moztrap-vendor-lib`_ repository. These are included as submodules of
this repository, at ``requirements/dist`` and ``requirements/vendor``
respectively.

.. _Selenium: http://seleniumhq.org
.. _moztrap-tests: https://github.com/mozilla/moztrap-tests
.. _moztrap-reqs: https://github.com/mozilla/moztrap-reqs
.. _moztrap-vendor-lib: https://github.com/mozilla/moztrap-vendor-lib

Sample local.py for lomoztrap
-----------------------------

Sample::

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "db",
            "USER": environ.get("USER", ""),
            "PASSWORD": "",
            "OPTIONS": {
                "init_command": "SET storage_engine=InnoDB",
                },
            "STORAGE_ENGINE": "InnoDB"
            }
        }

    USE_BROWSERID = False

    HMAC_KEYS = {
        "default": "override this"
    }

    BASE_PASSWORD_HASHERS = (
        'django_sha2.hashers.BcryptHMACCombinedPasswordVerifier',
        'django_sha2.hashers.SHA512PasswordHasher',
        'django_sha2.hashers.SHA256PasswordHasher',
        'django.contrib.auth.hashers.SHA1PasswordHasher',
        'django.contrib.auth.hashers.MD5PasswordHasher',
        'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher'
    )

    from django_sha2 import get_password_hashers
    PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)
