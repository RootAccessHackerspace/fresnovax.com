import os
import pipes

from pathlib import Path

import sass

def postBuild(site):
    node_modules = Path(site.path, 'node_modules')
    input_dir = Path(site.paths['static'], 'sass')
    output_dir = Path(site.paths['build'], 'static/css')

    if not output_dir.exists():
        os.makedirs(output_dir)

    for path in input_dir.glob('*.sass'):
        compiled_path = Path(output_dir, f'{path.stem}.css')
        compiled_css = sass.compile(
            filename=os.fspath(path),
            include_paths=(
                os.fspath(input_dir),
                os.fspath(node_modules)
            ),
            output_style='compressed',
        )

        with open(compiled_path, 'w') as f:
            f.write(compiled_css)
