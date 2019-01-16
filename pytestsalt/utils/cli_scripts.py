# -*- coding: utf-8 -*-
'''
    pytestsalt.utils.cli_scripts
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to generate Salt CLI scripts for test runs
'''

# Import Python Libs
from __future__ import absolute_import, unicode_literals
import os
import stat
import logging
import textwrap

log = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

SCRIPT_TEMPLATES = {
    'salt': textwrap.dedent(
        '''
        from salt.scripts import salt_main

        if __name__ == '__main__':
            salt_main()
        '''
    ),
    'salt-api': textwrap.dedent(
        '''
        import salt.cli

        def main():
            sapi = salt.cli.SaltAPI()
            sapi.start()

        if __name__ == '__main__':
            main()'
        '''
    ),
    'common': textwrap.dedent(
        '''
        from salt.scripts import salt_{0}
        import salt.utils.platform

        def main():
            if salt.utils.platform.is_windows():
                import os.path
                import py_compile
                cfile = os.path.splitext(__file__)[0] + '.pyc'
                if not os.path.exists(cfile):
                    py_compile.compile(__file__, cfile)
            salt_{0}()

        if __name__ == '__main__':
            main()
        '''
    )
}


def generate_script(bin_dir,
                    script_name,
                    executable,
                    code_dir,
                    extra_code=None,
                    inject_sitecustomize=False):
    '''
    Generate script
    '''
    # Late import
    import pytestsalt.utils.compat as compat

    if not os.path.isdir(bin_dir):
        os.makedirs(bin_dir)

    cli_script_name = 'cli_{}.py'.format(script_name.replace('-', '_'))
    script_path = os.path.join(bin_dir, cli_script_name)

    if not os.path.isfile(script_path):
        log.info('Generating %s', script_path)

        with compat.fopen(script_path, 'w') as sfh:
            script_template = SCRIPT_TEMPLATES.get(script_name, None)
            if script_template is None:
                script_template = SCRIPT_TEMPLATES.get('common', None)
            if script_template is None:
                raise RuntimeError(
                    'Pytest Salt\'s does not know how to handle the {} script'.format(
                        script_name
                    )
                )

            script_contents = textwrap.dedent(
                '''
                #!{executable}

                import sys

                CODE_DIR = r'{code_dir}'
                if CODE_DIR not in sys.path:
                    sys.path.insert(0, CODE_DIR)
                '''.format(
                    executable=executable,
                    code_dir=code_dir
                )
            )

            if extra_code:
                script_contents += '\n' + extra_code + '\n'

            if inject_sitecustomize:
                script_contents += textwrap.dedent(
                    '''
                    # Allow sitecustomize.py to be importable for test coverage purposes
                    SITECUSTOMIZE_DIR = r'{sitecustomize_dir}'
                    if SITECUSTOMIZE_DIR not in sys.path:
                        sys.path.insert(0, SITECUSTOMIZE_DIR)
                    '''.format(
                        sitecustomize_dir=os.path.join(
                            ROOT_DIR, 'salt', 'coverage'
                        )
                    )
                )

            script_contents += '\n' + script_template.format(script_name.replace('salt-', ''))
            sfh.write(script_contents.strip())
            log.debug(
                'Wrote the following contents to temp script %s:\n%s',
                script_path,
                script_contents
            )
        fst = os.stat(script_path)
        os.chmod(script_path, fst.st_mode | stat.S_IEXEC)

    log.info('Returning script path %r', script_path)
    return script_path
