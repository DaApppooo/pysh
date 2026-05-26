"""
Pysh is a small set of tools to run common shell commands independently of the
OS it's running on. Pysh is not intended to compile anything for apple products.
PYSH IS NOT SUPPOSED TO BE INSTALLED VIA A PACKAGE MANAGER SUCH AS PIPY.
Pysh is intended to run on a recent version of python.

To use pysh simply run `git submodule add <url-of-where-pysh-is>` in your git
project and then write `from psyh.pysh import *` in your script.

Here are the commands you can use once you imported pysh:
- is_windows() : check if you're on windows
- current_target() : Returns 'Linux' or 'Windows' depending on what you're on.
- pinfo(msg, end='\\n') : Print info (if DO_NOTHING is False).
- pwarn : Print warning (if DO_NOTHING is False). 
- perr : Print error (if DO_NOTHING is False).
- has_program(name) : Returns true if an executable with the given name exists and is
  accessible using $PATH (or %PATH%).
- need_program(name) : Asks `has_program`, and if not, prints an error and quits.
- shell(s: str | list[str], crash=True, hide=False, help: str|None=None, direct_output=True)
  : Runs the s command in a subshell. If crash is True, then if the status code isn't 0 the
    program will quit with the same status code. Won't show the command being run if hide
    is True. If help isn't None and the command returned a non-zero status code, the given
    string will be shown. If direct_output is False, the stdout of the program won't be
    shown until the subshell closed. If crash is False, this command will return a
    CalledProcessError if the subshell ends with a nonzero status-code. Otherwise
    stdout will be returned as a python string. This command won't do anything
    if DO_NOTHING is True.
- chdir(path) : Use this to temporarily change directory. Here's how to use it:
  with chdir(my_path):
    # Do something in my_path
    pass
  # Now you're not in my_path anymore
- wget(src, dst) : Will download the content of src (a url) and save it as the
  given destination.
- extract(src, dst, archive_ext=None) : Will extract src into dst. If dst
  doesn't exist and src contains multiple files or folders, dst will be created.
  If the archive has, at the top level, only one directory, its content will be
  put in the dst directory. If the archive has, at the top level, only one
  file, dst is expected to be a file path, and this file will be moved to dst.
  If src contains, at the top level, multiple files or folders, these will be
  moved in the dst folder. This method is not 100% safe when multithreaded
  (although collisions are very, very, very unlikely). You can specify the
  extension for the src archive with archive_ext.
- archive(src, dst) : Will archive src into dst. If src is a single string,
  then the content of this file or directory will be put in the archive without
  a directory at the top level. If src is a list of strings, these strings must
  be paths to files or directories that exists, and these will be put at the
  top level of dst. If you want to have a directory that contains the other
  stuff you want in your archive at the top level, you can make a temporary
  directory in which you put everything, and use that temporary directory as
  dst.
- rm(path) : will remove recursively (if necessary) the given file/folder.
  If the file or folder doesn't exists nothing will happen.
- ensure_dir(path) : This command will make sure the given path is a directory.
  If that path doesn't exists but can be created (there isn't a file in between)
  it will be created. If the path is a file or goes through a file this command
  will show an error and quit.
- cp(src, dst) : Copies (recursively if necessary) the given src to dst.
  Behaves exactly like `cp -r` on Linux.
- mv(src, dst) : Will move src into dst. If src ends with `*` shell globbing
  will apply (won't work if it's not at the end), except that paths that begin
  with a dot will be included. Otherwise, similar to `mv` on Linux.
- ls(path) : Will return the list of files/folders in the given path with the
  given path append to the name of the files/folders. You can give an empty
  path which will be substitued with '.'. Doesn't list recursively.
- lsr(path, fltr: Callable[[str], bool] = ...) : Same as ls(path) but lists
  recursively and applies the given filter. By default there's no filter.
- cat(path) : Reads the file in text format and returns a python string of the
  whole file. This can fail if there are errors when decoding the bytes of the
  file into a text form, if the file is a directory or if the file doesn't
  exists.
- cat_bin(path) : Reads the file in binary format and returns a bytearray/bytes
  of the whole file. Similar failure points as cat(path) except that no
  decoding happens.
- write(path, text) : Writes the given text (which can also be a
  bytearray/bytes object) in a file at path. Will fail if the given path is a
  directory. Warning: will overwrite files.
- make_exec(path) : Ensure the given file can be run as an executable. Useful
  only on linux. But can help make a script more OS independent.
- sep() : Returns the path separator in the current OS.
- exec_local(path) : Completes a relative path to make it executable.
  (a -> ./a)

Exposed functions:
- isdir(path) : Returns true if the given path is a directory.
- isabs(path) : Returns true if the given path is an absolute path.
- isfile(path) : Returns ... you get it.
- islink(path) : if it's a link/shortcut.
- join(p1, p2, p3, ...) : Join different elements or paths together using the
  proper path separator based on the current OS.
- exists(path) : if the path exists.
- sha1 : Returns the sha1 hexdigest/checksum of the given string.
- sha256 : same but for sha256
- md5 : same but for md5

Classes:
- ScriptSet : see internal class documentation.
- Package : see internal class documentation.

Scripts provided with pysh:
- install_c_compiler_windows() : as the name suggests, installs a c and c++
  compiler on windows. Will crash on linux.

"""

import shutil
import os
import pathlib
import config
import subprocess as subp
from platform import system
from os.path import isdir, isabs, isfile, islink, join, exists
from collections import Callable
import hashlib
from random import randint

DO_NOTHING = False
_PYSH_REQUIREMENTS = None

def is_windows():
  return system() == 'Windows'
def current_target():
  return system()

def pinfo(msg, end = '\n'):
  if DO_NOTHING:
    return
  print("[INFO]", msg, end=end)
def pwarn(msg, end='\n'):
  if DO_NOTHING:
    return
  print("[\x1b[1;33mWARN\x1b[0m]", msg, end=end)
def perr(msg, end='\n'):
  if DO_NOTHING:
    return
  print("[\x1b[1;31mERR\x1b[0m]", msg, end=end)
def has_program(name: str):
  return bool(shutil.which(name))
def need_program(name: str):
  if DO_NOTHING:
    _PYSH_REQUIREMENTS.append(name)
    return
  if not has_program(name):
    perr(f"Missing program {name!r}.")
    quit(1)

def shell(s: str | list[str], crash = True, hide = False, help: str | None = None, direct_output: bool = True):
  if DO_NOTHING:
    return
  if not isinstance(s, str):
    s = ' && '.join(s)
  if config.VERBOSE and not hide:
    print(f"\x1b[1;32m$\x1b[0m {s}")
  if config.TARGET == 'Windows':
    res = subp.run(s, encoding='utf-8', check=False, capture_output=not direct_output, shell=True, executable='C:\\Windows\\system32\\cmd.exe')
  else:
    res = subp.run(s, encoding='utf-8', check=False, capture_output=not direct_output, shell=True)
  out = res.stdout
  if out and not hide:
    print(res.stdout)
  if res.stderr and not hide:
    print(res.stderr)
  if res.returncode:
      perr(f"Exited with status code {res.returncode}.")
      if help is not None:
          pinfo(help)
      if crash:
          quit(res.returncode)
      return subp.CalledProcessError(res.returncode, s, out, res.stderr)
  if out:
    return out.strip()
  else:
    return out
class chdir:
  def __init__(self, p: str):
    if DO_NOTHING:
      return
    self.prev = os.getcwd()
    os.chdir(p or '.')
  def __enter__(self):
    pass
  def __exit__(self, *a):
    if DO_NOTHING:
      return
    os.chdir(self.prev)
def wget(src: str, dst: str):
  if DO_NOTHING:
    return
  if config.TARGET == 'Windows':
    shell(f"powershell wget '{src}' -OutFile '{dst}'")
  else:
    shell(f"wget '{src}' -O '{dst}'")
def extract(src: str, dst: str, archive_ext: str | None = None):
  """
  Will extract archive 'src' in directory 'dst'.
  If 'src' contains a folder which contains X, X will be moved into 'dst'.
  Otherwise, the content of 'src' is moved into 'dst'.
  """
  if DO_NOTHING:
    return
  tmp = f'_extract_tmp{os.getpid()}{randint(0, 9999999999999999)}'
  ensure_dir(tmp)
  try:
    shutil.unpack_archive(src, tmp, archive_ext)
    content = ls(tmp)
    print(content)
    if len(content) > 1:
      ensure_dir(dst)
      mv(os.path.join(tmp, '*'), dst)
    elif len(content) == 0:
      pwarn(f"Extracted empty archive '{src}'.")
    elif os.path.isdir(content[0]):
      mv(os.path.join(content[0], '*'), dst)
    else:
      mv(os.path.join(content[0], '*'), dst)
  except:
    raise
  finally:
    rm(tmp)
def archive(src: str | list[str], dst: str):
  """
  Will archive 'src' in 'dst'.
  """
  if DO_NOTHING:
    return
  tmp = f'_archive_tmp{os.getpid()}{randint(0, 9999999999999)}'
  ensure_dir(tmp)
  try:
    _dst = pathlib.Path(dst)
    if isinstance(src, str):
      if os.path.isdir(src):
        cp(os.path.join(src, '*'), tmp)
      else:
        cp(src, tmp)
    else:
      for p in src:
        cp(p, tmp)
    shutil.make_archive(_dst.stem, _dst.suffix[1:], tmp, "")
  except:
    raise
  finally:
    rm(tmp)
def rm(path: str):
  if DO_NOTHING:
    return
  if not os.path.exists(path):
    return
  pinfo(f"Removing {path}.")
  assert path is not "/", "wtf... seriously ? check the scripts you run before running them, please."
  if os.path.isdir(path):
    shutil.rmtree(path)
  else:
    os.remove(path)
def ensure_dir(path):
  if DO_NOTHING:
    return
  if not os.path.exists(path):
    os.makedirs(path)
  elif not os.path.isdir(path):
    perr(f"Path {path} should be a directory.")
    quit(1)
def cp(src: str, dst: str):
  if DO_NOTHING:
    return
  ensure_dir(os.path.dirname(dst))
  pinfo(f"Copying '{src}' to '{dst}'.")
  if os.path.isdir(src):
    shutil.copytree(src, dst)
  else:
    shutil.copyfile(src, dst)
def mv(src: str, dst: str, shush = False):
  if DO_NOTHING:
    return
  if d := os.path.dirname(dst):
    ensure_dir(d)
  else:
    ensure_dir(dst)
  if not shush:
    pinfo(f"Moving '{src}' to '{dst}'.")
  if src.endswith('*'):
    path, search = src.rsplit(config.SEPARATOR, 1)
    search = search[:-1]
    srcs = [
      i
      for i in ls(path)
      if i.rsplit(config.SEPARATOR,1)[-1].startswith(search)
    ]
    src_ = src
    for src in srcs:
      mv(src, dst, shush=True)
  else:
    if os.path.isdir(dst):
      os.rename(src, os.path.join(dst, src.rsplit(config.SEPARATOR, 1)[-1]))
    else:
      os.rename(src, dst)
def ls(p: str):
  if DO_NOTHING:
    return []
  if not p:
      p = '.'
  return [ os.path.join(p, i) for i in os.listdir(p) ]
def lsr(p: str, fltr = lambda x : True):
  if DO_NOTHING:
    return []
  l = []
  for i in ls(p):
    if os.path.exists(os.path.join(i, '.git')):
        continue
    if os.path.isdir(i):
        l.extend(lsr(i, fltr))
    elif fltr(i):
        l.append(i)
  return l

def cat_bin(path) -> bytes:
  if DO_NOTHING:
    return b""
  if not isfile(path):
    perr(f"{path!r} is not a file. Cannot read content.")
    quit(1)
  with open(path, "rb") as f:
    return f.read()
def cat(path) -> str:
  if DO_NOTHING:
    return ""
  if not isfile(path):
    perr(f"{path!r} is not a file. Cannot read content.")
    quit(1)
  with open(path, "r") as f:
    return f.read()
def write(path, text: str | bytes):
  if DO_NOTHING:
    return
  if isdir(path):
    perr(f"{path!r} is a dir. Cannot write.")
    quit(1)
  if isinstance(text, str):
    text = text.encode("utf-8")
  with open(path, "wb") as f:
    f.write(text)
def make_exec(path):
  """ Make file executable. """
  if DO_NOTHING:
    return
  if current_target() == "Linux":
    shell(f"chown +x {path!r}")
def sep():
  if current_target() == "Windows":
    return "\\"
  return "/"
def exec_local(path):
  """ Complete path to make a relative path executable as a command (my_bin -> ./my_bin). """
  if sep() in path:
    return path
  return os.path.join(".", path)

# Common checksums utilities
def make_hexdigester(hasher) -> str:
  def _f(s: str):
    return hasher(s).hexdigest()
  return _f
sha1 = make_hexdigester(hashlib.sha1)
sha256 = make_hexdigester(hashlib.sha256)
md5 = make_hexdigester(hashlib.md5)

class ScriptSet:
  """
  A set of scripts.

  Example:
  setup = ScriptSet("Setup") # the name is optional

  @setup.linux
  def my_os_dependent_setup():
    pass
  @setup.windows
  def my_os_dependent_setup():
    pass
  @setup.linux
  @setup.windows
  def my_other_setup():
    setup.requires(my_os_dependent_setup)
    # this one works on both linux and windows
    pass

  setup.run() # Will run every script based on the current OS
  """
  
  def __init__(self, name: str | None = "Unnamed script."):
    self.name = name
    self.scripts = {'Linux':[], 'Windows':[]}
    self.current_script = None
    self.run_id = 0
  def collect_requirements() -> list[str]:
    global _PYSH_REQUIREMENTS, DO_NOTHING
    pwarn(f"Auto-collecting requirements for {self.name!r}. It's not guaranteed nothing will happen.")
    _PYSH_REQUIREMENTS = []
    DO_NOTHING = True
    target = current_target()
    self.run_id += 1
    for idx, (script, run_id) in enumerate(self.scripts[target]):
      if run_id < self.run_id:
        self.current_script = script.__name__
        script()
      self.scripts[target][idx][1] = self.run_id
    L = _PYSH_REQUIREMENTS
    _PYSH_REQUIREMENTS = None
    DO_NOTHING = False
    pinfo("Here are the requirements:\n" + '\n'.join(L))
    return L
  def linux(self, f):
    self.scripts['Linux'].append([f, 0])
    return f
  def windows(self, f):
    self.scripts['Windows'].append([f, 0])
    return f
  def require(self, name: str | Callable):
    if isinstance(name, str):
      pinfo(f"{self.current_script!r} requires {name!r}...")
    else:
      pinfo(f"{self.current_script!r} requires {name.__name__!r}...")
    target = current_target()
    old_script = self.current_script
    for s in self.scripts[target]:
      if (
         (isinstance(name, str) and s[0].__name__ == name)
      or (s[0].__name__ == name.__name__)
      ):
        if s[1] < self.run_id:
          s[1] = self.run_id
          self.current_script = script.__name__
          s[0]()
          self.current_script = old_script
          pinfo(f"Back to {self.current_script!r}...")
        else:
          pinfo("Which was already ran.")
        return
  def run(self, parallelizer: Callable[[Callable[[],None]],None] = None):
    """
      You can give a parallelizer that will run however you want the given script.
      Note that requirements won't work well with parallelization as no
      algorithm is written to correctly handle both of those things. Make
      different script sets for different steps if you want to have both.

      Here's the default parallelizer: lambda f: f()
    """
    if parallelizer is None:
      parallelizer = lambda f: f()
      para = ""
    else:
      para = " (parallelized)"
    target = current_target()
    self.run_id += 1
    for idx, (script, run_id) in enumerate(self.scripts[target]):
      if run_id < self.run_id:
        pinfo(f"{self.name}{para}: {repr(script.__name__)}...")
        self.current_script = script.__name__
        parallelizer(script)()
      self.scripts[target][idx][1] = self.run_id
    pinfo(f"{self.name}: Done !")

def install_c_compiler_windows():
  """
  Script to install a C compiler if you're on windows.
  """
  shell("winget install -e --id JonathanMarler.msvcup")

class Package:
  """
  Just the association of:
  - a setup/install script set
  - a clean/uninstall script set
  - an update script set (optional)
  - a setup/installed detection function

  Here's an example:
  my_package = Package("my_package")

  @my_package.setup.linux
  @my_package.setup.windows
  def hello_world():
    need_program("echo")
    shell("echo hello world >hello_world.txt")

  @my_package.clean.linux
  @my_package.clean.windows
  def good_bye():
    rm("hello_world.txt")
  
  @my_package.is_setup
  def check_setup():
    return exists("hello_world.txt")

  my_package.run_setup()
  my_package.run_setup() # Won't run a second time.
  print(cat("hello_world.txt"))
  my_package.run_clean_up()
  """
  def __init__(self, name = "unnamed_package"):
    self.setup = ScriptSet(f"Setting up {name!r}")
    self.clean = ScriptSet(f"Cleaning up {name!r}")
    self.update = ScriptSet(f"Updating {name!r}")
    self._is_setup: Callable[[], bool] = lambda: False
    self.name = name
  def collect_requirements() -> list[str]:
    return self.setup.collect_requirements()
  def run_setup(self, parallelizer = None):
    """ For docs about the parallelizer see ScriptSet.run """
    if self._is_setup():
      pinfo(f"{self.name!r} is already setup.")
    else:
      self._setup.run(parallelizer)
  def run_clean_up(self):
    if not self._is_setup():
      pinfo(f"{self.name!r} isn't there, nothing to clean.")
    else:
      self._clean.run()
  def run_update(self):
    self._update.run()
  def is_setup(self, f: Callable):
    self._is_setup = f
    return f
  
    
