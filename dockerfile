FROM docker.io/agturley/rhel7-python3:3.6.8

RUN useradd --user-group --create-home --no-log-init --shell /bin/bash superset

# Install nodejs for custom build
# https://superset.incubator.apache.org/installation.html#making-your-own-build
# https://nodejs.org/en/download/package-manager/

WORKDIR /home/superset

COPY artifacts/requirements.txt .
COPY artifacts/requirements-dev.txt .
COPY artifacts/mysql80-community-release-el7-3.noarch.rpm .
COPY artifacts/pgdg-redhat-repo-latest.noarch.rpm .


RUN yum update -y \
&& yum install -y mysql80-community-release-el7-3.noarch.rpm pgdg-redhat-repo-latest.noarch.rpm \
&& curl https://packages.microsoft.com/config/rhel/7/prod.repo > /etc/yum.repos.d/mssql-release.repo \
&& curl -sL https://rpm.nodesource.com/setup_10.x | bash - \
&& yum install -y nodejs gcc gcc-c++ libffi-devel openssl-devel libsas12-devel openldap-devel unixODBC unixODBC-devel sqlite-devel \
&& ACCEPT_EULA=Y yum install msodbcsql17 mssql-tools -y \
&& yum install -y postgresql11 postgresql11-devel mysql-community-devel \
&& yum clean all


RUN pip3 install --upgrade setuptools pip \
    && pip3 install -r requirements.txt -r requirements-dev.txt \
    && pip3 install gevent pysqlite3 python-ldap pyodbc \
    && rm -rf /root/.cache/pip


COPY artifacts/incubator-superset/superset /home/superset/superset

ENV PATH=/home/superset/superset/bin:$PATH \
    PYTHONPATH=/home/superset/superset/:$PYTHONPATH \
    FLASK_APP=superset


RUN cd superset/assets \
    && npm config set python python3.7 \
    && npm ci \
    && npm run build \
    && rm -rf node_modules

#RUN pip3 install superset

COPY artifacts/docker-init.sh .
COPY artifacts/docker-entrypoint.sh /entrypoint.sh
#COPY generic superset_config.py
COPY artifacts/superset_config.py /home/superset/superset/superset_config.py

RUN chown -R superset:superset /home/superset

USER superset
# Setting LC_ALL and LANG to en_US.UTF-8 to get Click to work
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8088 8443
