from fabric.api import env, local, task
import itertools

class BaseConfSettings:
    project= 'breeze'
    repo_url= 'ssh://github-private/linked/breeze.git'
    shell= '/bin/bash -l -c'
    github_user= 'linked'
    github_token= '5e39ba021637bc494b16103333b9692f'
    directory= '/www/breeze'
    sql_root_pass= '17204105102701720570127'
    project_db_name= 'breeze'
    sql_user= 'lwbreeze'
    sql_pass= 's0eezy'
    def __iter__(self):
        for attr in dir(self):
            if attr.startswith('__'): continue
            yield attr, getattr(self, attr)

class VagrantSettings(BaseConfSettings):
    process_owner= 'vagrant'
    user= 'vagrant'
    web_hosts = ['127.0.0.1:2222']
    roles = {'web': web_hosts }
    hosts= web_hosts

class AwsClusterSettings(BaseConfSettings):
    process_owner= 'linked'
    user= 'linked'
    web_hosts = ['lwbreez.us']
    roles = {'web': web_hosts}
    hosts = web_hosts


@task
def web():
    use_role('web')

def use_role(name='web'):
    if not hasattr(env, 'cluster'):
        use_cluster('vagrant')
    if env.cluster == 'vagrant':
        if name == 'all': name = 'web'
        running = local('vagrant status | grep %s'%(name), capture=True)
        if not 'running' in running:
            local('vagrant up')
        result = local('vagrant ssh-config %s | grep IdentityFile'%name, capture=True)
        env.key_filename = result.split()[1].replace('"','')
    if hasattr(env.conf, 'key_filename'):
        env.key_filename = env.conf.key_filename
    env.hosts = env.conf.roles[name]

def use_cluster(name='vagrant'):
    if name == 'vagrant':
        env.conf = VagrantSettings()
    elif name == 'aws':
        env.conf = AwsClusterSettings()
    env.user = env.conf.user
    env.root_dir = "/www/breeze"
    env.cluster = name

@task
def vagrant():
    use_cluster('vagrant')

@task
def aws():
    use_cluster('aws')

default_env = web
