from bottle import route, run, template,redirect, static_file, request
import sys
import os

HOMEDIR=os.path.dirname(os.path.abspath(sys.argv[0]))

S_NAME	= 0
S_URL	= 1
S_DESC	= 2
S_HIDE	= 3
HIDDEN	= 1
PUBLIC	= 0

def read_settings():
  fn = HOMEDIR + "/settings.txt"
  settings = {
    'masterkey': 'replace-this-with-something-else',
    'title': 'go.py'
  }

  f = open(fn,"r")
  for line in f:
    line = line.strip()
    if not line:
      continue
    if line[0] == '#':
      continue
    line = line.split('=',1)
    if len(line) != 2:
      continue
    settings[line[0]] = line[1]
  f.close()

  return settings

def read_services():
  file = HOMEDIR + "/routes.txt"
  services = []

  f = open(file,'r')
  for line in f:
    line = line.strip()
    if not line:
      continue
    if line[0] == '#':
      continue
    line = line.split(maxsplit=2)
    if len(line) < 2:
      continue
    elif len(line) == 2:
      line[S_DESC] = line[S_NAME]

    if line[S_NAME][0] == '-':
      line.append(HIDDEN)
      line[S_NAME] = line[S_NAME][1:]
    else:
      line.append(PUBLIC)
    services.append(line)

  f.close()

  services.sort()
  return services

def read_file(file):
  with open(file,"r") as fh:
    return fh.read()

def render_welcome(items,show_hidden = False,msg=""):
  settings = read_settings()
  templ = read_file(HOMEDIR + "/welcome.html")
  disp = []
  for item in items:
    if (not show_hidden) and item[S_HIDE] == HIDDEN:
      continue
    disp.append({
      'url': item[S_URL],
      'name': item[S_NAME],
      'desc': item[S_DESC]
    })
  return template(templ, items=disp, title=settings['title'] , msg=msg)

def jump(targets, extra):
  if len(targets) == 1:
    redirect(targets[0][S_URL]+extra)
    return "Redirecting..."

  upubs = []
  for item in targets:
    if item[S_HIDE]:
      continue
    upubs.append(item)

  if len(upubs) == 1:
    redirect(upubs[0][S_URL]+extra)
    return "Redirecting..."
  elif len(upubs) == 0:
    return index(msg = "No routes found!")

  return render_welcome(upubs, msg="Maching routes...")

def search(name,extra):
  settings = read_settings()
  if name == settings['masterkey']:
    return index(True)
    
  name = name.lower()
  services = read_services()

  # simple match...
  for item in services:
    if item[S_NAME] == name:
      return jump([item],extra)

  # Try a simple string match...
  matches = []
  for item in services:
    if item[S_NAME].find(name) != -1 or item[S_DESC].lower().find(name) != -1:
      matches.append(item)
  if len(matches) > 0:
    return jump(matches,extra)

  return index(msg= "Route \""+name+"\" not found...")

def io_syslog(fh,tag):
  r,w = os.pipe()
  cpid = os.fork()
  if cpid == 0:
    # Child...
    os.close(w)
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()
    fin = os.fdopen(r)

    # ~ x = open('log-%s.txt' % tag,'w')
    import syslog
    
    for line in fin:
      line = line.rstrip()
      if not line: continue
      syslog.syslog("%s: %s" % (tag,line))
      # ~ x.write("%s: %s\n" % (tag,line))
      # ~ x.flush()
    sys.exit(0)

  os.close(r)
  os.dup2(w, fh.fileno())
  os.close(w)

############################################################
# routes
############################################################

@route('/favicon.ico')
def favicon():
  return static_file('favicon.ico',root=HOMEDIR)

@route('/static/<file:path>')
def assets(file):
  return static_file(file,root=HOMEDIR + "/static")

@route('/<name>/<more:path>')
def generic_path(name,more):
  return search(name,more)

@route('/<name>')
def simple_path(name):
  return search(name,'')

@route('/<name>/')
def simple_path(name):
  return search(name,'')

@route('/',method='POST')
def post_search():
  if request.forms.get('go'):
    return search(request.forms.get('go'),'')
  return index()

@route('/')
def index(show_hidden = False, msg=""):
  services = read_services()
  return render_welcome(services,show_hidden,msg)


############################################################
# main
############################################################

if __name__ == "__main__":
  listen='localhost'
  port=8005

  for opt in sys.argv[1:]:
    if opt.startswith('--listen='):
      listen = opt[9:]
    elif opt.startswith('--port='):
      port = int(opt[7:])
    elif opt.startswith('--pid='):
      with open(opt[6:],'w') as fh:
       fh.write("%d\n" % os.getpid())
    elif opt.startswith('--syslog='):
      io_syslog(sys.stdout,'%s(out)' % opt[9:])
      io_syslog(sys.stderr,'%s(err)' % opt[9:])
    elif opt == '--detach' or opt == '-d':
      res = os.fork()
      if res > 0:
       # Running on parent...
       sys.exit(0)
       os.setsid()
      print("Running as %d" % os.getpid())
    else:
      sys.stderr.write("Unknown option %s\n" % opt)

  
  run(host=listen, port=port)

