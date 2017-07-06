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

 # load triples
g = rdflib.Graph()
result = g.load("http://sfsheath.github.io/roman-amphitheaters/roman-amphitheaters.geojson", format="json-ld")

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
    result = g.query("""SELECT * 
           WHERE {
             ?id geojson:properties[ dcterms:title ?title  ; ramphsprops:chronogroup ?chronogroup] .

             OPTIONAL { ?id geojson:properties[ramphsprops:dimensions [ ramphsprops:arena-major ?arenamajor] ] }
             OPTIONAL { ?id geojson:properties[ramphsprops:dimensions [ ramphsprops:arena-minor ?arenaminor] ] }
             OPTIONAL { ?id geojson:properties[ramphsprops:dimensions [ ramphsprops:exterior-major ?extmajor] ] }
             OPTIONAL { ?id geojson:properties[ramphsprops:dimensions [ ramphsprops:exterior-minor ?extminor] ] }
             OPTIONAL { ?id geojson:properties[ramphsprops:moderncountry ?moderncountry] }
             OPTIONAL { ?id geojson:properties[ramphsprops:province ?province] }  
             OPTIONAL { ?id geojson:properties[ramphsprops:region ?region] }           
     
             } """ , initNs = ns)
           
    
    rdoc = dominate.document(title="Searchable List of Roman Amphitheaters")
    rdoc.head += meta(charset="utf-8")
    rdoc.head += meta(http_equiv="X-UA-Compatible", content="IE=edge")
    rdoc.head += meta(name="viewport", content="width=device-width, initial-scale=1")
    rdoc.head += link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/css/bootstrap.min.css")
    rdoc.head += link(rel="stylesheet", href="https://cdn.datatables.net/1.10.15/css/dataTables.bootstrap.min.css")
    rdoc.head += script(src="https://code.jquery.com/jquery-2.2.4.min.js")
    rdoc.head += script(src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/js/bootstrap.min.js")
    rdoc.head += script(src="https://cdn.datatables.net/1.10.15/js/jquery.dataTables.min.js")
    rdoc.head += script(src="https://cdn.datatables.net/1.10.15/js/dataTables.bootstrap.min.js")
    rdoc.head += script("""$(document).ready(function() {
    $('#ramphs').DataTable( {
        'paging':   false
    } );
} );""")
    with rdoc:
        with div(cls="container"):
            h1("Roman Amphitheaters and Related Buildings")
            with p():
                span("See ")
                a("http://github.com/sfsheath/roman-amphitheaters", href="http://github.com/sfsheath/roman-amphitheaters")
                span(" for data and overview.")
            with table(id="ramphs"):
                with thead():
                    th("Label")
                    th("Country")
                    th("Region or Province")
                    th("Ext. Major")
                    th("Ext. Minor")
                    th("Arena Major")
                    th("Arena Minor")
                with tbody():
                    for r in result:
                        with tr():
                            td(str(r.title))

                            if str(r.moderncountry) != 'None':
                                td(str(r.moderncountry))
                            else:
                                td("")
                            
                            if str(r.region) != 'None':
                                td(str(r.region).replace('http://purl.org/roman-amphitheaters/resource/',''))
                            elif str(r.province) != 'None':
                                td(str(r.province).replace('http://purl.org/roman-amphitheaters/resource/',''))
                            else:
                                td("")

                            if str(r.extmajor) != 'None':
                                td(str(r.extmajor))
                            else:
                                td("")

                            if str(r.extminor) != 'None':
                                td(str(r.extminor))
                            else:
                                td("")

                            if str(r.arenamajor) != 'None':
                                td(str(r.arenamajor))
                            else:
                                td("")

                            if str(r.arenaminor) != 'None':
                                td(str(r.arenaminor))
                            else:
                                td("")
    return rdoc.render()


# display # of triples to show it's working
@app.route('/ramphs/graph')
def ramphs_graph():
    

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

                    


    
    

    