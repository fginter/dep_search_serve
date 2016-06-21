#!/usr/bin/env python3

from flask import Flask, Markup
import flask
import json
import requests
import urllib

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
        elif line.startswith("# hittoken"):
            current_tree.append(line)
        elif not line.startswith("#"):
            current_tree.append(line)
        if line=="":
            current_comment.append(Markup(current_context))
            yield "\n".join(current_tree), current_comment
            current_comment=[]
            current_tree=[]
            current_context=""


class Query:

    @classmethod
    def from_formdata(cls,fdata):
        query=fdata['query'].strip()
        hits_per_page=int(fdata['hits_per_page'])
        treeset=fdata['treeset'].strip()
        if fdata.get('case'):
            case_sensitive=True
        else:
            case_sensitive=False
        return(cls(treeset,query,case_sensitive,hits_per_page))

    @classmethod
    def from_get_request(cls,args):
        query=args["search"]
        treeset=args["db"]
        case_sensitive=True
        hits_per_page=10
        return(cls(treeset,query,case_sensitive,hits_per_page))

    def __init__(self,treeset,query,case_sensitive,hits_per_page):
        self.treeset,self.query,self.case_sensitive,self.hits_per_page=treeset,query,case_sensitive,hits_per_page

    def query_link(self,url=""):
        return url+"query?search={query}&db={treeset}&case_sensitive={case_sensitive}&hits_per_page={hits_per_page}".format(query=urllib.parse.quote(self.query),treeset=self.treeset,case_sensitive=self.case_sensitive,hits_per_page=self.hits_per_page)

    def download_link(self,url=""):
        return DEP_SEARCH_WEBAPI+"?search={query}&db={treeset}&case={case_sensitive}&retmax=5000&dl".format(query=urllib.parse.quote(self.query),treeset=self.treeset,case_sensitive=self.case_sensitive)
        
@app.route("/")
def index():
    r=requests.get(DEP_SEARCH_WEBAPI+"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)
    return flask.render_template("index_template.html",corpus_groups=metadata["corpus_groups"])

#This is what JS+AJAX call
@app.route('/query',methods=["POST"])
def query_post():
    q=Query.from_formdata(flask.request.form)
    r=requests.get(DEP_SEARCH_WEBAPI,params={"db":q.treeset, "case":q.case_sensitive, "context":3, "search":q.query, "retmax":q.hits_per_page})
    if r.text.startswith("# Error in query"):
        ret = flask.render_template("query_error.html", err=r.text)
    elif not r.text.strip():
        ret = flask.render_template("empty_result.html")
    else:
        ret=flask.render_template("result_tbl.html",trees=yield_trees(r.text.splitlines()))
    return json.dumps({'ret':ret,'query_link':q.query_link(),'download_link':q.download_link()});

#This is what GET calls
#We return the index and prefill a script call to launch the form for us
@app.route('/query',methods=["GET"])
def query_get():
    r=requests.get(DEP_SEARCH_WEBAPI+"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)

    if "db" not in flask.request.args or "search" not in flask.request.args:
        return flask.render_template("get_help.html",corpus_groups=metadata["corpus_groups"])

    q=Query.from_get_request(flask.request.args)
    run_request=Markup('dsearch_simulate_form("{treeset}","{query}","{case_sensitive}","{max_hits}");'.format(treeset=q.treeset,query=q.query.replace('"',r'\"'),case_sensitive=q.case_sensitive,max_hits=q.hits_per_page))
    return flask.render_template("index_template.html",corpus_groups=metadata["corpus_groups"],run_request=run_request)
    


if __name__ == '__main__':
    app.run(debug=DEBUGMODE)
    r=requests.get(DEP_SEARCH_WEBAPI+"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)

