from flask import Flask
import flask
import json
import requests

DEBUGMODE=True
try:
    from config_local import * #use to override the constants above if you like
except ImportError:
    pass #no config_local

app = Flask("dep_search_webapp")

def yield_trees(src):
    current_tree=[]
    for line in src:
        current_tree.append(line)
        if line=="":
            yield "\n".join(current_tree)
            current_tree=[]

@app.route("/")
def index():
    return flask.render_template("index_template.html")

@app.route('/query',methods=["POST"])
def query():
    query=flask.request.form['query'].strip()
    hits_per_page=int(flask.request.form['hits_per_page'])
    if flask.request.form.get('case'):
        case_sensitive=True
    else:
        case_sensitive=False
    
    r=requests.get(DEP_SEARCH_WEBAPI,params={"db":"Suomi24", "case":case_sensitive, "search":query, "retmax":hits_per_page},stream=True)
    ret=flask.render_template("result_tbl.html",trees=yield_trees(l.decode("utf-8") for l in r.iter_lines()))
    return json.dumps({'ret':ret});

if __name__ == '__main__':
    app.run(debug=DEBUGMODE)
