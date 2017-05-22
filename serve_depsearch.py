#!/usr/bin/env python3

# This code can run in both Python 2.7+ and 3.3+

from flask import Flask, Markup
import flask
import json
import requests
import six
import six.moves.urllib as urllib  # use six for python 2.x compatibility
import traceback

DEBUGMODE=False
try:
    from config_local import * #use to override the constants above if you like
except ImportError:
    pass #no config_local

app = Flask("dep_search_webgui")

def yield_trees(src):
    current_tree=[]
    current_comment=[]
    current_context=u""
    for line in src:
        if line.startswith(u"# visual-style"):
            current_tree.append(line)
        elif line.startswith(u"# URL:"):
            current_comment.append(Markup(u'<a href="{link}">{link}</a>'.format(link=line.split(u":",1)[1].strip())))
        elif line.startswith(u"# context-hit"):
            current_context+=(u' <b>{sent}</b>'.format(sent=flask.escape(line.split(u":",1)[1].strip())))
        elif line.startswith(u"# context"):
            current_context+=(u' {sent}'.format(sent=flask.escape(line.split(u":",1)[1].strip())))
        elif line.startswith(u"# hittoken"):
            current_tree.append(line)
        elif not line.startswith(u"#"):
            current_tree.append(line)
        if line==u"":
            current_comment.append(Markup(current_context))
            yield u"\n".join(current_tree), current_comment
            current_comment=[]
            current_tree=[]
            current_context=u""


class Query:

    @classmethod
    def from_formdata(cls,fdata):
        query=fdata[u'query'].strip()
        hits_per_page=int(fdata[u'hits_per_page'])
        treeset=fdata[u'treeset'].strip()
        if fdata.get(u'case'):
            case_sensitive=True
        else:
            case_sensitive=False
        return(cls(treeset,query,case_sensitive,hits_per_page))

    @classmethod
    def from_get_request(cls,args):
        query=args[u"search"]
        treeset=args[u"db"]
        case_sensitive=True
        hits_per_page=10
        return(cls(treeset,query,case_sensitive,hits_per_page))

    def __init__(self,treeset,query,case_sensitive,hits_per_page):
        self.treeset,self.query,self.case_sensitive,self.hits_per_page=treeset,query,case_sensitive,hits_per_page

    def query_link(self,url=u"",treeset=None):
        if treeset is None:
            treeset=self.treeset
        if six.PY2:
            return url+u"query?search={query}&db={treeset}&case_sensitive={case_sensitive}&hits_per_page={hits_per_page}".format(query=unicode(urllib.parse.quote(self.query.encode("utf-8")),"utf-8"),treeset=treeset,case_sensitive=self.case_sensitive,hits_per_page=self.hits_per_page)
        else:
            return url+u"query?search={query}&db={treeset}&case_sensitive={case_sensitive}&hits_per_page={hits_per_page}".format(query=urllib.parse.quote(self.query),treeset=treeset,case_sensitive=self.case_sensitive,hits_per_page=self.hits_per_page)

    def download_link(self,url=""):
        if six.PY2:
            return DEP_SEARCH_WEBAPI+u"?search={query}&db={treeset}&case={case_sensitive}&retmax=5000&dl".format(query=unicode(urllib.parse.quote(self.query.encode("utf-8")),"utf-8"),treeset=self.treeset,case_sensitive=self.case_sensitive)
        else:
            return DEP_SEARCH_WEBAPI+u"?search={query}&db={treeset}&case={case_sensitive}&retmax=5000&dl".format(query=urllib.parse.quote(self.query),treeset=self.treeset,case_sensitive=self.case_sensitive)
        
@app.route(u"/")
def index():
    r=requests.get(DEP_SEARCH_WEBAPI+u"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)
    return flask.render_template(u"index_template.html",corpus_groups=metadata[u"corpus_groups"])

#This is what JS+AJAX call
@app.route(u'/query',methods=[u"POST"])
def query_post():
    try:
        sources=[]
        q=Query.from_formdata(flask.request.form)
        r=requests.get(DEP_SEARCH_WEBAPI,params={u"db":q.treeset, u"case":q.case_sensitive, u"context":3, u"search":q.query, u"retmax":q.hits_per_page})
        if r.text.startswith(u"# Error in query"):
            ret = flask.render_template(u"query_error.html", err=r.text)
        elif not r.text.strip():
            ret = flask.render_template(u"empty_result.html")
        else:
            lines=r.text.splitlines()
            if lines[0].startswith("# SourceStats : "):
                sources=json.loads(lines[0].split(" : ",1)[1])
                ret=flask.render_template(u"result_tbl.html",trees=yield_trees(lines[1:]))
            else:
                ret=flask.render_template(u"result_tbl.html",trees=yield_trees(lines))
        links=['<a href="{link}">{src}</a>'.format(link=q.query_link(treeset=src),src=src) for src in sources]
        return json.dumps({u'ret':ret,u'source_links':u' '.join(links),u'query_link':q.query_link(),u'download_link':q.download_link()});
    except:
        traceback.print_exc()
        

#This is what GET calls
#We return the index and prefill a script call to launch the form for us
@app.route(u'/query',methods=[u"GET"])
def query_get():
    r=requests.get(DEP_SEARCH_WEBAPI+u"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)

    if u"db" not in flask.request.args or u"search" not in flask.request.args:
        return flask.render_template(u"get_help.html",corpus_groups=metadata[u"corpus_groups"])

    q=Query.from_get_request(flask.request.args)
    run_request=Markup(u'dsearch_simulate_form("{treeset}","{query}","{case_sensitive}","{max_hits}");'.format(treeset=q.treeset,query=q.query.replace(u'"',u'\\"'),case_sensitive=q.case_sensitive,max_hits=q.hits_per_page))
    return flask.render_template(u"index_template.html",corpus_groups=metadata[u"corpus_groups"],run_request=run_request)
    


if __name__ == u'__main__':
    app.run(debug=DEBUGMODE)
    r=requests.get(DEP_SEARCH_WEBAPI+u"/metadata") #Ask about the available corpora
    metadata=json.loads(r.text)

