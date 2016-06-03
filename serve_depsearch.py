from flask import Flask
import flask
import json
import requests

try:
    from config_local import * #use to override the constants above if you like
except ImportError:
    pass #no config_local

app = Flask("dep_search_webapp")

@app.route("/")
def index():
    return flask.render_template("index_template.html")

@app.route('/query',methods=["POST"])
def nearest():
    query=flask.request.form['query'].strip()
    hits_per_page=int(flask.request.form['hits_per_page'])
    ret=flask.render_template("result_tbl.html",query=query)
    return json.dumps({'ret':ret});

if __name__ == '__main__':
    app.run(debug=DEBUGMODE)
