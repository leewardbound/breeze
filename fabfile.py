from base_fabric import *
import os, sys

@task
def nginx():
    fsudo('service nginx restart')

@task
def bootstrap():
    web()
    fsudo('apt-get update -y')
    fsudo('mkdir -p /www/')
    ubuntu_dev_tools()
    shortcuts()
    install_mysql()
    #clone_repo()
    install_redis()
    install_nginx()
    install_php5()
    #install_php_hiphop()
    sdo('update-rc.d nginx defaults')
    db()
    ubuntu_dev_tools()
    shortcuts()
    install_redis()
    install_mysql()
    install_php5()
    syn13()
    ubuntu_dev_tools()
    shortcuts()
    install_redis()
    install_mysql()
    install_nginx()
    install_php5()

@task
def install_php_hiphop():
    fsudo('apt-add-repository -y ppa:mapnik/boost')
    fsudo('apt-get update')
    apt('software-properties-common gdebi-core')
    #fsudo('gdebi tools/hhvm-fastcgi.deb')
    fsudo('gdebi -yq /project/tools/hhvm.deb')
    fsudo('update-rc.d hhvm defaults')

@task
def restart_php_hiphop():
    fsudo('service hhvm restart')

@task
def install_php5():
    apt('php5-fpm php-mail php5-mysql')
    restart_php5()

@task
def restart_php5():
    fsudo('service php5-fpm restart')

@task
def get_dat_files():
    for dat in ['GeoIP', 'GeoIPCity', 'GeoIPOrg']:
        if not fexists('/www/{project}/%s.dat'%dat):
            frun("wget -O /www/{project}/%s.dat http://lwb.co/%s.dat"%(dat,dat))

def is_vagrant():
    return fexists('/vagrant')

@task
def deploy():
    nginx()
    restart_supervisor()

@task
def shortcuts():
    fsudo('apt-get install -yq vim zsh tmux bc')
    fsudo('chsh -s /bin/zsh {user}')
    if not fexists('.zshrc'):
        frun('wget -O .zshrc http://lwb.co/.zshrc')

@task
def uname():
    frun('uname -a')

@task
def hostname():
    frun('hostname')

@task
def ls():
    frun('ls {directory}')

def speak(msg, wait=False):
    local('echo "%s" | say%s'%(msg, wait and ' ' or ' &'))
