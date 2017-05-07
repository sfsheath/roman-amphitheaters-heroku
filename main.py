import html

# because dominate will stop on html
pyhtml = html

import os
import re
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

import dominate
from dominate.tags import *

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for, after_this_request

import json
import markdown
import numpy as np
import pandas as pd
import pymysql.cursors
import rdflib

# pandas options

pd.set_option('max_colwidth', 1000)

# namespace
ns = {"dcterms" : "http://purl.org/dc/terms/",
      "geojson" : "https://purl.org/geojson/vocab#",
      "owl"     : "http://www.w3.org/2002/07/owl#",
      "rdf"     : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
      "rdfs"    : "http://www.w3.org/2000/01/rdf-schema#",
      "ramphsprops" : "http://purl.org/roman-amphitheaters/properties#",
      "ramphs" :  "http://purl.org/roman-amphitheaters/resource/" }


# initiate the webserver
app = Flask(__name__)


#default
@app.route('/')
def index():
    return "<html><head><style></style></head><body><b>Hello</b></body></html>"

# display # of triples to show it's working
@app.route('/ramphs/graph')
def ramphs_graph():
    
    # load triples
    g = rdflib.Graph()
    result = g.load("http://sfsheath.github.com/roman-amphitheaters/roman-amphitheaters.geojson", format="json-ld")

    # simple query to get a one line result that confirms basic setup is working
    result = g.query("SELECT (count(?s) as ?cnt) WHERE { ?s ?p ?o }")
    for r in result:
        triplecnt = r.cnt
    
    # See https://pyformat.info for formatting python strings
    return "Total triples after g.load: {}".format(triplecnt)

# display table from mysql 
@app.route('/ramphs/tables')
def ramphs_tables():
    # connect to mysql
    connection = pymysql.connect(host='hosting.nyu.edu',
                             user='sebastia_adsqro',
                             password = os.environ.get('MYSQL_PW'),
                             db='sebastia_adsq',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    sql = "select * from ramphs"
    
    # parse result so it's ready to be turned into a dataframe
    with connection.cursor() as cursor:

        cursor.execute(sql)
        names = [ x[0] for x in cursor.description]
        result = cursor.fetchall()

    df = pd.DataFrame(result, columns = names)
    
    return """<html>
<head>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/r/bs-3.3.5/jq-2.1.4,dt-1.10.8/datatables.min.css"/>
 
<script type="text/javascript" src="https://cdn.datatables.net/r/bs-3.3.5/jqc-1.11.3,dt-1.10.8/datatables.min.js"></script>

<script type="text/javascript">
$(document).ready(function() {
    $('.dataframe').DataTable();
} );
</script>

    </head>%s</html>""" % df.to_html()

    
    
# display info for single amphitheater
@app.route('/ramphs/id/<path:amphitheater>')
def ramphs_id(amphitheater):
    
    # load data, but we're going to make this faster
    g = rdflib.Graph()
    result = g.load("http://sfsheath.github.com/roman-amphitheaters/roman-amphitheaters.geojson", format="json-ld")
    
    result = g.query("""SELECT DISTINCT ?property ?value
           WHERE {
             { ramphs:%s geojson:properties ?props .
              ?props ?property ?value . }
            
            UNION { ramphs:%s geojson:properties/ramphsprops:dimensions ?blank . ?blank ?property ?value }
            UNION { ramphs:%s geojson:properties/ramphsprops:capacity ?blank . ?blank ?property ?value }
            
            FILTER (!isBlank(?value))
           } """ % (amphitheater,amphitheater,amphitheater), initNs = ns)
           
    df = pd.DataFrame(result.bindings)
    
    return """<html>
    <body>
     <h1>{}</h1>
     {}
     </body>
     </html>""".format(amphitheater, df.to_html())


# display a popup list of amphitheaters
@app.route('/ramphs/popup')
def ramphs_popup():
    # connect to mysql
    connection = pymysql.connect(host='hosting.nyu.edu',
                             user='sebastia_adsqro',
                             password = os.environ.get('MYSQL_PW'),
                             db='sebastia_adsq',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    sql = "select id from ramphs"
    
    # parse result so it's ready to be turned into a dataframe
    with connection.cursor() as cursor:

        cursor.execute(sql)
        names = [ x[0] for x in cursor.description]
        result = cursor.fetchall()

    df = pd.DataFrame(result, columns = names)
    
    rdoc = dominate.document(title="Select an Amphitheater (dominate test)")
    
    with rdoc:
        h1("Select an amphitheater")
        with form(action = "/ramphs/showid"):
            with select(name="id"):
                for r in df.iterrows():
                    option(str(r[1]['id']))
            input(type="submit")
    
    
    return rdoc.render()


# handle popup action
@app.route('/ramphs/showid')
def ramphs_showid():
   id = request.args.get('id')
   # basically, just redirect to the URL that can show info for a single amphitheater
   return redirect("/ramphs/id/{}".format(id), code=302)

                    


    
    

    