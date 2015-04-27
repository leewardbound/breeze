import os, sys
from fabric.api import run, sudo, cd, puts, settings, hide, execute, prompt
from envs import *
import fabric


def fformat(cmd):
    new_cmd = cmd.format(**dict(env.conf))
    return new_cmd

@task
def frun(cmd):
    if not getattr(env, 'conf', ''): default_env()
    run(fformat(cmd))

@task
def fexists(cmd):
    if not getattr(env, 'conf', ''): default_env()
    return fabric.contrib.files.exists(fformat(cmd))

@task
def fsudo(cmd):
    if not getattr(env, 'conf', ''): default_env()
    sudo(fformat(cmd))


def _prepare():
    with settings( hide('warnings','stdout'), warn_only=True):
        fsudo("export DEBCONF_TERSE=yes DEBIAN_PRIORITY=critical DEBIAN_FRONTEND=noninteractive")

@task
def apt(pkg):
    _prepare()
    with settings( hide('warnings','stdout'), warn_only=True ):
        fsudo("apt-get -qqyu install %s" % pkg)

def has_apt(pkg):
    with settings( hide('warnings','stdout'), warn_only=True ):
        result = fsudo('dpkg --status %s | grep "ok installed" ' % pkg)
        return result.succeeded

@task
def ubuntu_dev_tools():
    """
    Install a fresh ubuntu instance
    """
    fsudo('apt-get update -qqy')
    apt("ntp vim python-setuptools python-dev git-core subversion mercurial unzip \
        zsh screen libevent-dev libevent-dev build-essential openssl libssl-dev curl \
        sqlite3 libsqlite3-dev ruby ri bzr python-software-properties \
        openjdk-6-jre-headless python-pygraphviz screen libcurl4-openssl-dev \
        libxml2-dev libxslt1-dev git libtiff4-dev libopenjpeg-dev libopenjpeg2 libjpeg-dev libjpeg8-dev zlib1g-dev \
        libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk python-pip")
    fsudo("pip install virtualenv==1.10.1 virtualenvwrapper --upgrade #--no-use-wheel")
    fsudo("mkdir -p /www/logs")
    #frun('whoami')
    install_redis()
    #install_node()
    #install_sass()
    install_closure()
    install_pillow()

@task
def install_redis():
    """
    Install redis
    """
    fsudo('wget http://lwb.co/install-redis.sh -O install-redis.sh')
    fsudo('bash install-redis.sh')
    return
    ##keep all this below in case we may need it again
    arch = 'arch' in env and env['arch'] or 'amd64'
    if fexists('`which redis-cli`'): print("redis-cli is exists")
    if not fexists('`which redis-cli`'): print("redis-cli not exists")
    if fexists('`which redis-cli`'): return
    fsudo(
        'wget -O redis.deb http://ftp.us.debian.org/debian/pool/main/r/redis/redis-server_2.4.9-1_%s.deb'%arch)
    fsudo(
        'wget -O libjemalloc-dev.deb http://ftp.us.debian.org/debian/pool/main/j/jemalloc/libjemalloc-dev_2.2.5-1_%s.deb'%arch)
    fsudo(
        'wget -O libjemalloc1.deb http://ftp.us.debian.org/debian/pool/main/j/jemalloc/libjemalloc1_2.2.5-1_%s.deb'%arch)
    fsudo('dpkg -i libjemalloc1.deb')
    fsudo('dpkg -i libjemalloc-dev.deb')
    fsudo('dpkg -i redis.deb')
    fsudo('update-rc.d redis defaults')

@task
def install_node():
    """
    Clone node from github and make, install
    """
    #fsudo('add-apt-repository ppa:gezakovacs/coffeescript')
    #fsudo('apt-get update -qqy')
    #apt('coffeescript')
    #return
    #if(exists('`which node`') and exists('`which npm`')): return

    if(fexists('`which node`')): return
    frun('git clone -q git://github.com/joyent/node.git')
    with cd('node'):
        frun('./configure && make &> /dev/null')
        fsudo('make install')
        frun('npm install coffee-script')

@task
def install_sass(force=False):
    """
    Install compass through gem
    """
    #if fexists('`which node`'): return
    fsudo('gem install compass sass --no-rdoc --no-ri -q --pre')
    #fsudo('compass install blueprint')

def install_closure(force=False):
    """
    Wget, extract, and install closure
    """
    if fexists('`which closurec`'): return
    zip = 'http://closure-compiler.googlecode.com/files/compiler-latest.zip'
    fsudo('wget %s -O ~/closure.zip'%zip)
    fsudo('mkdir -p /etc/closure')
    fsudo('cd /etc/closure && unzip ~/closure.zip')
    fsudo('echo \
          "#!/bin/sh \n exec java -jar /etc/closure/compiler.jar $*" > \
          /usr/local/bin/closurec')
    fsudo('chmod a+x /usr/local/bin/closurec')
    fsudo('chmod -R a+r /etc/closure/')

@task
def install_postgresql():
    apt('postgresql libpq-dev binutils libgeos-dev libgeos-c1 \
        binutils libproj-dev postgis postgresql-9.1-postgis gdal-bin gdal-contrib')
    apt('libmysqlclient-dev')
    apt("apt-get install postgresql postgresql-contrib python-dev postgresql-server-dev-all")
    fsudo("apt-get build-dep -yyqq python-psycopg2")
    fsudo("pip install psycopg2")
    fsudo("wget -O postgis.sh https://docs.djangoproject.com/en/dev/_downloads/create_template_postgis-debian.sh")
    fsudo("sed -i 's/-E UTF8/-E UTF8 --locale en_US.utf8 -T template0 /' postgis.sh")
    fsudo(""" echo "createdb --locale en_US.utf8 -T template_postgis {project_db_name};" >>postgis.sh""")
    fsudo(""" echo psql -c \\\\"create user {sql_user} WITH PASSWORD \\'{sql_pass}\\'\\;\\\\" >>postgis.sh""")
    fsudo(""" echo psql -c \\\\"GRANT ALL ON DATABASE {project_db_name} to {sql_user}\\;\\\\" >>postgis.sh""")
    fsudo(""" echo psql -c \\\\"alter user {sql_user} createdb\\;\\\\" >>postgis.sh""")
    fsudo("chown postgres:postgres postgis.sh")
    fsudo("chmod +x postgis.sh")
    fsudo("mv postgis.sh /tmp/postgis.sh")
    with settings(hide('warnings','stdout',), warn_only=True):
        fsudo("sudo su - postgres -c 'bash /tmp/postgis.sh'")


def install_mysql():
    apt('debconf')
    #fsudo('echo phpmyadmin phpmyadmin/app-password-confirm select {sql_root_pass} | debconf-set-selections')
    apt('mysql-server libmysqlclient-dev python2.7-mysqldb')#phpmyadmin php5-mysql php5-cli'

    frun("""
mysql -uroot -p{sql_root_pass} -e "create database {project_db_name}; grant all on {project_db_name}.* to {sql_user}@'localhost' identified by '{sql_pass}';\" || echo "DB Probably already exists"
""")
    frun("""
mysql -uroot -p{sql_root_pass} -e "create database test_{project_db_name}; grant all on test_{project_db_name}.* to {sql_user}@'localhost' identified by '{sql_pass}';\" || echo "DB Probably already exists"
""")

def config(name):
    return env.config.default.get(name, False)

def config_dir():
    return env.root_dir
#return config('directory')

def pull(tag=None, directory='{directory}'):
    with cd(fformat(directory)):
        frun('git pull -q')
        if tag:
            frun('git reset --hard %s'%tag)

@task
def clone_repo(tag=None, project='{project}',repo='{repo_url}',directory='{directory}'):
    frun('mkdir -p ~/.ssh')
    #if local_exists('deploy/ssh.config'):
    if local_exists('deploy/ssh.config'):
        config = open('deploy/ssh.config').read()
        frun('echo "%s" > ~/.ssh/config'%config)
    if local_exists('deploy/known_hosts'):
        hosts = open('deploy/known_hosts').read()
        frun('echo "%s" > ~/.ssh/known_hosts'%hosts)
    if local_exists('$(pwd)/deploy/github-deploy-key'):
        key = open('deploy/github-deploy-key').read()
        frun('echo "%s" > ~/.ssh/github-deploy'%key)
        frun('chmod 0600 ~/.ssh/github-deploy')

    parent = '/'.join(fformat(directory).split('/')[:-1])
    if fexists('%s/.git/config'%directory):
        pull(tag, directory)
    elif fexists(directory):
        print 'Fragments of an old directory found left over... Attempting to delete it...'
        prevent_horrible_accidents()
        fsudo('rm -rf %s'%directory)
    elif parent:
        fsudo('mkdir -p %s'%parent)
        fsudo('chown -R {user}:{user} %s'%parent)
        with cd(parent):
            frun('git clone -q %s {directory} || cd {directory} && git pull'%(repo))
            if tag:
                frun('git reset --hard %s'%tag)


WORDLIST_PATHS = [os.path.join('/', 'usr', 'share', 'dict', 'words')]
DEFAULT_MESSAGE = "Are you sure you want to do this?"
WORD_PROMPT = '  [%d/%d] Type "%s" to continue (^C quits): '

def prevent_horrible_accidents(msg=DEFAULT_MESSAGE, horror_rating=1):
    import random
    """Prompt the user to enter random words to prevent doing something stupid."""

    valid_wordlist_paths = [wp for wp in WORDLIST_PATHS if os.path.exists(wp)]

    if not valid_wordlist_paths:
        print('Attempting to prevent a horrible accident, but no wordlists found!')
        exit()

    with open(valid_wordlist_paths[0]) as wordlist_file:
        words = wordlist_file.readlines()

    print msg

    for i in range(int(horror_rating)):
        word = words[random.randint(0, len(words))].strip()
        p_msg = WORD_PROMPT % (i+1, horror_rating, word)
        answer = prompt(p_msg, validate=r'^%s$' % word)
        if not answer:
            print "Failed to type the challenge correctly, exiting"
            exit()


@task
def pip_install_requirements():
    ensure_virtualenv()
    reqs = [ "requirements/project.txt",
            "project.txt"]
    with cd(env.conf.directory):
        for req in reqs:
            req = '{directory}/%s'%req
            if fexists(req):
                puts("Bootstrapping from %s"%req)
                vcmd("pip install -q --requirement %s"%req)
                return

def is_vagrant():
    return fexists('/vagrant')

@task
def name_your_system_please():
    fn = fformat('{directory}/.system_name')
    if is_vagrant() and not fexists(fn):
        answer = prompt("""
Uh oh! No system name found!
        **** HEY YOU **** READ THIS ***
        **** HEY YOU **** READ THIS ***
        **** HEY YOU **** READ THIS ***
        YOU MUST BE NEW HERE! Because we don't yet have a name for your system!
        Adding a system name (in %s) helps our debug team
        follow your errors and figure out where our issues are located!

        THAT'S OK, I'll make one for you now!
        Please enter your system name, all lowercase, no punctuation:
                        """%fn, validate=r'^[a-zA-Z]+$')

        if not answer:
            print "Failed to give a valid name, EXITING AND QUITTING EVERYTHING"
            exit()
        frun('echo %s > %s'%(answer,fn))

def ensure_virtualenv():
    frun('mkdir -p {venv_wrapper_home}')
    fsudo('[[ -e /www/.virtualenvs ]] || ln -s {venv_wrapper_home} /www/.virtualenvs')
    if not fexists('{venv_wrapper_home}/{project}/bin/python'):
        with cd(env.conf.venv_wrapper_home):
            frun('virtualenv {project} --no-site-packages')
            frun('source {venv_wrapper_home}/{project}/bin/activate')
            if is_vagrant():
                local('vagrant reload')


@task
def install_nginx():
    fsudo('add-apt-repository -y ppa:nginx/development')
    fsudo('apt-get update')
    apt('nginx')
    conf = '/etc/nginx/sites-enabled/{project}'
    if fexists(conf): fsudo('rm -f %s'%conf)
    fsudo('rm -rf /etc/nginx/nginx.conf')
    fsudo('ln -s /project/deploy/nginx.conf /etc/nginx/nginx.conf')
    fsudo('/etc/init.d/nginx stop')
    fsudo('/etc/init.d/nginx start')
    fsudo('update-rc.d nginx defaults')


@task
def django_init():
    with cd(env.conf.directory):
        fsudo('mkdir -p /www/logs/')
        fsudo('touch {project}.log && chmod 777 {project}.log')
        fsudo('[[ -e /www/logs/{project}.log ]] || ln -s `pwd`/{project}.log /www/logs/')
        #manage('importsassframeworks')
        collectstatic()
        fsudo('chown -R {user}:{user} _generated_media')
        manage('generatemedia')
        manage('syncdb --noinput --no-initial-data')

@task
def loaddata():
    with cd(env.conf.directory):
        manage('loaddata fixtures/basic_data.json')

@task
def install_supervisord():
    fsudo('pip install supervisor==3.0b2')
    venv('pip install gunicorn')
    fsudo('rm -rf /etc/supervisord.conf')
    fsudo('rm -rf /etc/supervisord.conf.d')
    fsudo('rm -rf /etc/init.d/supervisord')
    fsudo('ln -s %s/deploy/supervisord.conf /etc'%env.conf.directory)
    fsudo('ln -s %s/deploy/supervisord.conf.d /etc'%env.conf.directory)
    fsudo('ln -s %s/deploy/supervisor.init /etc/init.d/supervisord'%env.conf.directory)
    fsudo('chmod +x /etc/init.d/supervisord')
    fsudo('mkdir -p /www/logs; touch /www/logs/supervisord.log && chmod 777 /www/logs/supervisord.log')
    fsudo('update-rc.d supervisord defaults')
    restart_supervisor()

def local_exists(path):
    s = "Failed checking for directory %s..."%path
    output = local("""/bin/bash -c "if [[ -e $(pwd)/%s ]] ; then echo ; else echo -n '%s' ; fi" """%(path,s))
    if s in output: return False
    return True

def vcmd(cmd=""):
    '''Run a virtualenv-based command in the site directory.  Usable from other commands or the CLI.'''
    if not cmd:
        sys.stdout.write(green("Command to run: %s/bin/" %
                               env.conf.venv_path.rstrip('/')))
        cmd = raw_input().strip()

    if cmd:
        with cd(env.conf.directory):
            total_cmd = env.conf.venv_path.rstrip('/') + '/bin/' + cmd
            print total_cmd
            frun(total_cmd)

@task
def start_supervisor():
    fsudo('/etc/init.d/supervisord start')

@task
def stop_supervisor():
    fsudo('/etc/init.d/supervisord stop')

@task
def restart_supervisor():
    import time
    stop_supervisor()
    time.sleep(4)
    fsudo("ps -ef | grep python | grep -v grep | awk '{{print $2}}' | xargs sudo kill -9 || true")
    time.sleep(1)
    start_supervisor()

@task
def collectstatic():
    '''Collect static media.'''
    with cd(env.conf.directory):
        manage('collectstatic --noinput --verbosity=0')

@task
def manage(cmd=""):
    '''Run a manage command in the site directory.  Usable from other commands or the CLI.'''
    if not cmd:
        sys.stdout.write(fabric.colors.green("manage.py command to run: "))
        cmd = raw_input().strip()
    name_your_system_please()
    if cmd:
        with cd(env.conf.directory):
            return frun(python('manage.py %s'%cmd))

def venv(cmd):
    if env.conf.venv_wrapper_home:
        return '{venv_wrapper_home}/{project}/bin/'+cmd
    return cmd

def python(cmd=''):
    return '%s %s'%(venv('python'),cmd)

#def exists(path):
#    s = "Failed checking for directory %s..."%path
#    with settings(hide('warnings','stdout', 'running'), warn_only=True):
#        outputs = frun('[[ -e %s ]] || echo -n "%s"'%(path,s))
#    for output in outputs:
#        if "Failed" in output: return False
#    return True
@task
def sdo(cmd=""):
    '''Sudo a command in the site directory.  Usable from other commands or the CLI.'''
    if not cmd:
        sys.stdout.write(fabric.colors.green("Command to run: sudo "))
        cmd = raw_input().strip()

    if cmd:
        with cd(env.conf.directory):
            fsudo(cmd)

@task
def rsp():
    return runserver_plus()

@task
def supervisor_all_but_gunicorn():
    sdo('sudo service supervisord start')
    sdo('sudo supervisorctl stop {project}')

@task
def runserver_plus():
    name_your_system_please()
    with cd(env.conf.directory):
        with settings(hide('warnings',), warn_only=True):
            frun("tmux new -d -s rsp || true")
            frun("tmux send -t rsp C-c")
            sdo('sudo service supervisord start')
            sdo('sudo supervisorctl stop {project}')
            return frun("tmux send -t rsp '" + python('manage.py runserver_plus 0.0.0.0:{gunicorn_port}') +"' C-m")
