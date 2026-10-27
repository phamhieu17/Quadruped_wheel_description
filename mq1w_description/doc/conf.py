"""Sphinx configuration of the mq1w_description documentation: English, with the Vietnamese translation in vi/.
    pip install -r ../../doc_requirements.txt
    sphinx-build -W doc doc/_build/html          (from mq1w_description/)"""
import os
import xml.etree.ElementTree as ET

project = 'mq1w_description'
author = 'MythMaker'
release = ET.parse(os.path.join(os.path.dirname(__file__), '..', 'package.xml')).getroot().findtext('version')
version = release
extensions = []
exclude_patterns = ['_build']
try:
    import sphinx_rtd_theme  # noqa: F401
    html_theme = 'sphinx_rtd_theme'
except ImportError:
    html_theme = 'alabaster'
