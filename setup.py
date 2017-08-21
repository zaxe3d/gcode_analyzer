from distutils.core import setup
import commands


def get_git_version():
    output = commands.getoutput("git describe - -abbrev = 0 - -tags")
    if "fatal" in output:
        return None
    return output


def get_download_url():
    git_version = get_git_version()
    if git_version is None:
        return None
    return 'https://github.com/zaxe3d/gcode_analyzer/archive/%s.tar.gz' % git_version

setup(
  name='gcode_analyzer',
  packages=['gcode_analyzer'],  # this must be the same as the name above
  version='1.0',
  description='GCode Analyzer Tool',
  author='Can Gelis',
  author_email='geliscan@gmail.com',
  url='https://github.com/zaxe3d/gcode_analyzer',
  download_url=get_download_url(),
  keywords=['gcode', '3d', 'analyzer'],
  classifiers=[]
)