# Startup

* get joseki, loomp and neonion
    * `git clone ssh://git@stash.ag-nbi.de:7999/an/joseki.git`
    * `git clone ssh://git@stash.ag-nbi.de:7999/an/loomp-server.git`
    * `git clone ssh://git@stash.ag-nbi.de:7999/an/neonion.git`


## Run on your local machine

For joseki and loomp you will need java 1.7 and grails 2.3.7 ([Groovy enVironment Manager](http://gvmtool.net) is a nice tool to get started with grails). For neonion you need python with django installed.


# tools und shell
`sudo apt-get install vim git joe tmux curl`

# (optional) nice bash config
`wget nutz.noova.de/rdot -O - | bash -s`

# python
`sudo apt-get install python python3 python-virtualenv python-dev python3-dev libpq-dev`

# java 1.7
`sudo apt-add-repository ppa:webupd8team/java`
`sudo apt-get update`
`sudo apt-get install oracle-java7-installer`

# elasticsearch
`wget -qO - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -`
`sudo echo "deb http://packages.elasticsearch.org/elasticsearch/1.3/debian stable main" >> /etc/apt/sources.list`
`sudo apt-get update`
`sudo apt-get install elasticsearch`
`sudo /etc/init.d/elasticsearch start`

# grails
`curl -s get.gvmtool.net | bash`
`gvm install grails 2.3.7`
`source ~/.gvm/bin/gvm-init.sh`


the following steps need one shell each:

* **joseki**
    * `cd joseki`
    * `java -server -Xmx512m -cp "lib/*" -Dlog4j.configuration=file:etc/log4j.properties joseki.rdfserver`


* **loomp-server**
    * `grails war`
    * `java $JAVA_OPTS -jar server/jetty-runner.jar --port 8080 target/*.war`


* **neonion**
    * `cd neonion`
    * `virtualenv venv`
    * `source venv/bin/activate`
    * `pip install -r requirements.txt` (you may need some python-dev stuff installed on your machine)
    * `python manage.py runserver`









## Run on heroku

* **joseki**
    * `cd joseki`
    * `heroku create`
    * `git push heroku master`
    * you will see the URL of your heroku app in the shell, it looks like http://foo-bar-1234.herokuapp.com/



* **loomp-server**
    * `cd loomp-server`
    * change the parameters `loomp.endpoint.query_url` and `loomp.endpoint.update_url` in the config file (`grails-app/conf/Config.groovy`) according to the URL of the joseki URL.
    * `git add grails-app/conf/Config.groovy`
    * `git commit -m "updated joseki adress to config"`
    * `heroku create`
    * `git push heroku master`
    * Again you will see a heroku URL, this time for the loomp-server. Assign this URL to the `grails.serverURL` in the config file.
    * `git add grails-app/conf/Config.groovy`
    * `git commit -m "updated loomp-server adress to config"`
    * `git push heroku master`


* **neonion**
    * `cd neonion`
    * Change the `server:` parameter in the config file (`prototype/static/js/neonion.js`) to the loomp-server URL .
    * `git add prototype/static/js/neonion.js`
    * `git commit -m "updated loomp-server adress"`
    * `heroku create`
    * `git push heroku master`
