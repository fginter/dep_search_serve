from flask import Flask, Markup
import flask
import json
import requests

DEBUGMODE=True
try:
    from config_local import * #use to override the constants above if you like
except ImportError:
    pass #no config_local

app = Flask("dep_search_webgui")

def yield_trees(src):
    current_tree=[]
    current_comment=[]
    current_context=""
    for line in src:
        if line.startswith("# visual-style"):
            current_tree.append(line)
        elif line.startswith("# URL:"):
            current_comment.append(Markup('<a href="{link}">{link}</a>'.format(link=line.split(":",1)[1].strip())))
        elif line.startswith("# context-hit"):
            current_context+=(' <b>{sent}</b>'.format(sent=flask.escape(line.split(":",1)[1].strip())))
        elif line.startswith("# context"):
            current_context+=(' {sent}'.format(sent=flask.escape(line.split(":",1)[1].strip())))
        elif not line.startswith("#"):
            current_tree.append(line)
        if line=="":
            current_comment.append(Markup(current_context))
            yield "\n".join(current_tree), current_comment
            current_comment=[]
            current_tree=[]
            current_context=""

@app.route("/")
def index():
    r=requests.get(DEP_SEARCH_WEBAPI+"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)
    return flask.render_template("index_template.html",treesets=metadata["corpus_list"])

#This is what JS+AJAX call
@app.route('/query',methods=["POST"])
def query():
    query=flask.request.form['query'].strip()
    hits_per_page=int(flask.request.form['hits_per_page'])
    treeset=flask.request.form['treeset'].strip()
    if flask.request.form.get('case'):
        case_sensitive=True
    else:
        case_sensitive=False
    
    r=requests.get(DEP_SEARCH_WEBAPI,params={"db":treeset, "case":case_sensitive, "context":3, "search":query, "retmax":hits_per_page},stream=True)
    ret=flask.render_template("result_tbl.html",trees=yield_trees(l.decode("utf-8") for l in r.iter_lines()))
    return json.dumps({'ret':ret});

#This is what GET calls
#We return the index and prefill a script call to launch the form for us
@app.route('/query',methods=["GET"])
def query2():
    r=requests.get(DEP_SEARCH_WEBAPI+"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)

    if "db" not in flask.request.args or "search" not in flask.request.args:
        return flask.render_template("get_help.html",treesets=metadata["corpus_list"])
    corpus=flask.request.args["db"]
    query=flask.request.args["search"]
    case_sensitive="checked"
    max_hits="10"
    run_request=Markup('dsearch_simulate_form("{corpus}","{query}","{case_sensitive}","{max_hits}");'.format(corpus=corpus,query=query,case_sensitive=case_sensitive,max_hits=max_hits))
    return flask.render_template("index_template.html",treesets=metadata["corpus_list"],run_request=run_request)
    


if __name__ == '__main__':
    app.run(debug=DEBUGMODE)
    r=requests.get(DEP_SEARCH_WEBAPI+"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)

