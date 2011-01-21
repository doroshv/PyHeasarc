#!/usr/bin/env python
import urllib
import VOTable
import sys
import re
from numpy import array, float64
# to do: sanitize input (i.e. make switches for complicated args) 'Galactic: LII BII'

class heasarq(object):
    """Representation of heasarc query"""
    def __init__(self, table, position, radius=30, resolver="SIMBAD",time="",max_results=100,
    fields="Standard", order_by="", params="", coordsys='equatorial', equinox="2000", gifsize=0):
        self.table=table
        self.position=position
        self.radius=radius
        self.resolver=resolver
        self.time=time
        self.max_results=max_results
        self.gifsize=gifsize
        self.equinox=equinox
        self.order = order_by.lower()
        self.params = params
        if coordsys.lower()=='equatorial':
            self.coordsys="Equatorial: R.A. Dec"
        else:
            self.coordsys="Galactic: LII BII"
        if fields.lower()=='standard' or fields.lower()=='all':
            self.fields=fields.capitalize() # do varon reconstruction
            addvaron=False
        else:
            self.fields=fields
            addvaron=True
        # print self.fields
        querydic={"tablehead":"",\
                  "Action":"Query",\
                  "Coordinates":self.coordsys,\
                  "Equinox":self.equinox,\
                  "Radius":self.radius,\
                  "NR":self.resolver,\
                  "GIFsize":self.gifsize,\
                  "fields": self.fields,\
                  "Entry":self.position,\
                  "ResultMax": self.max_results,\
                  "Time":"",\
                  "displaymode":"VODisplay"}
        querydic['tablehead']="name%3dBATCHRETRIEVALCATALOG%5f2%2e0 "+ str(self.table)
        if self.order:
            querydic['sortvar']=self.order
        if self.params:
            paramlist = self.params.split(',')
            # print paramlist
            for par in paramlist:
                entry = re.findall('(.*?)([><=\*].*)',par)[0]
                # print entry
                querydic['bparam_'+entry[0].strip()]=entry[1].strip().replace('=','')
        self.url='http://heasarc.gsfc.nasa.gov/db-perl/W3Browse/w3query.pl?'+\
            urllib.urlencode(querydic)
        if addvaron:
            self.url+='&varon='+'&varon=+'.join(fields.replace(',',' ').replace(';',' ').split())
        f=urllib.urlopen(self.url)
        try:
            vot=VOTable.VOTable(source=f)
        except:
            print "Error parsing your query! Check your query, availability of requested fields in requested table and if heasarc is online"
            vot=False
        self.vot=vot
        f.close()
        if self.vot:
            data=self.transposed([self.vot.getData(x) for x in self.vot.getDataRows()])
            self.desc=dict([(str(x.name),str(self.vot.getData(x)[0])) for x in self.vot.getFields()])
            if self.fields.lower()=='standard' or self.fields.lower()=='all':
                self.fields=",".join(self.desc.keys())
            for f in self.desc.keys():
                g=f
                if f=='class': g=f+'_name'
                if len(data)>=self.vot.getColumnIdx(f) and len(data)>0:
                    setattr(self,g,(self.desc[f],self.flotify(data[self.vot.getColumnIdx(f)])))
                else:
                    setattr(self,g,(self.desc[f],[]))
        
    
    def transposed(self,lists):
        if not lists: return []
        return map(lambda *row: list(row), *lists)
    def flotify(self,x,dtype=float64):
        """take an array and if possible convert it to dtype"""
        try:
            return array(x, dtype=dtype) 
        except:
            return array(x)
    def pprint_text(self,outfile=sys.stdout,print_offset=False):
        """pretty print results as a text (tab-padded) table to screen or file (if filename is specified)"""
        out = []
        closef=False
        if outfile!=sys.stdout:
            outfile=open(outfile,'w')
            closef = True
        k = self.fields.split(',')
        if not print_offset:
            try:
                k.remove('Search_Offset')
            except:
                pass
        try:
            k.remove('unique_id')
        except:
            pass
        for x in k:
            out.append([eval("self."+x)[0]]+list(eval("self."+x)[1]))
        pprint_table(outfile, list(array(out).transpose()))
        if closef:
            outfile.close()
    def pprint_pdf(self, outfile, print_offset=False):
        """docstring for pprint_pdf"""
        out=[]
        tmp = open('tmp_bre.tex','w')
        k = self.fields.split(',')
        # print self.fields
        if not print_offset:
            try:
                k.remove('Search_Offset')
            except:
                pass
        try:
            k.remove('unique_id')
        except:
            pass
        # k.sort()
        # print k
        k = filter(lambda x:x!='',k)
        for x in k:
            out.append([eval("self."+x)[0]]+list(eval("self."+x)[1]))
        out = list(array(out).transpose())
        latex = """\\documentclass[]{article}
        \\usepackage[utf8]{inputenc}
        \\usepackage{longtable, lscape}
        \usepackage[hmargin=1cm,vmargin=1cm]{geometry}
        \\begin{document}
        \\begin{landscape}
        \\begin{longtable}{"""
        # print latex
        latex+=('p{'+str(int(21./len(out[0])))+'cm}|')*len(out[0])+"}\n"
        latex+="\\\\\n\\hline".join(["\t&\t".join(y) for y in out])+'\\\\'
        latex+="""\\
        \\end{longtable}
        \\end{landscape}
        \\end{document}
        """
        print >> tmp, latex
        tmp.close()
        import os
        os.system('pdflatex -interaction=batchmode tmp_bre.tex >/dev/null')
        os.system('mv tmp_bre.pdf '+outfile)
        os.system('rm -f tmp_bre*')
        import glob
        return glob.glob(outfile)

    
heasarc = heasarq
def format_num(num):
    """Format a number according to given places.
    Adds commas, etc.
    
    Will truncate floats into ints!"""

    try:
        inum = int(num)
        return locale.format("%.*f", (0, inum), True)

    except (ValueError, TypeError):
        return str(num)

def get_max_width(table, index):
    """Get the maximum width of the given column index
    """
    
    return max([len(format_num(row[index])) for row in table])

def pprint_table(out, table):
    """Prints out a table of data, padded for alignment
    
    @param out: Output stream ("file-like object")
    @param table: The table to print. A list of lists. Each row must have the same
    number of columns.
    
    """

    col_paddings = []
    
    for i in range(len(table[0])):
        col_paddings.append(get_max_width(table, i))

    for row in table:
        # left col
        print >> out, row[0].ljust(col_paddings[0] + 1),
        # rest of the cols
        for i in range(1, len(row)):
            col = format_num(row[i]).rjust(col_paddings[i] + 2)
            print >> out, col,
        print >> out

if __name__ == '__main__':
    help_msg = """
    The main purpose of this module is to provide batch access to
    http://heasarc.nasa.gov/ catalogue database from within python scripts. It
    can be used, however as standalone tool as well. the call sequence is:
    
    browse_extract table, position, radius=30, output="text_table|pdf",
    resolver="SIMBAD|NED",Time="", max_results=100, fields="Standard",
    order_by="", params="", coordsys='equatorial|galactic', equinox="2000|1950", GIFsize=0
    
    where "parameter=XX" means that it is optional and defaults to XX value.
    Required parameters are "table" and "position", and they shall be
    specified as table="XX", i.e. via standard syntax. Position may be given
    as name of the source or as coordinate string (standard heasarc
    conventions). List of tables and their descriptions may be obtained at
    
    http://heasarc.nasa.gov/db-perl/W3Browse/w3catindex.pl
    ** note that pdf output uses latex, so pdflatex and several commonly installed
    packages have to be available
    """
    import argparse
    parser = argparse.ArgumentParser(description='Access to heasarc catalogues', epilog=
    """
    See couple of examples below:\n\n
    1)To create a pdf with table listing all X-ray pulsars which exhibit a Cyclotron line in their spectra,
    ordered py spin period use:\n\n
    
    ./browse_extract.py hmxbcat "GX 301-2" -radius 1e8 -params "xray_type=*C*" -fields "name,ra,dec,porb,pulse_per" -order_by pulse_per -out pdf="test.pdf"\n\n
    2)To display on screen observation ids,exposure and PI name for  Crab observations by RXTE in 2007 type\n\n
    ./browse_extract.py xtemaster Crab -fields "obsid,exposure,pi_lname" -order_by exposure -time "2007-01-01..2007-12-31" -params='exposure>0' -out text_table\n\n
    """)
    parser.add_argument('table', metavar='table', type=str,help='heasarc table to query. See list on http://heasarc.nasa.gov/db-perl/W3Browse/w3catindex.pl')
    parser.add_argument('position', metavar='position', type=str,help='Position of the source, can be name or coordinates')    
    parser.add_argument('-radius', default=30, type=float, help='search radius in arcminutes')
    parser.add_argument('-output', default='text_table', help='output results as padded text (text_table) or pdf (pdf) table to file. If output to file desired please use -output text_table=file.txt')
    parser.add_argument('-resolver',default='SIMBAD', help='Name resolver can be SIMBAD (default) or NED')
    parser.add_argument('-time', default='', help="Restrict search to time interval defined according to heasarc conventions")
    parser.add_argument('-max_results', default=100, help="Maximum number of returned results")
    parser.add_argument('-fields', default="Standard", help="Output only specified fields of the table. Can be 'standard','all', or list of fields.")
    parser.add_argument('-order_by',default="", help="Sort output by specified field")
    parser.add_argument('-params', default='', help="Heasarc parametric search. Individual parameters are comma separated: param1>x, param2=*C* (same conventions as on website)")
    parser.add_argument('-coordsys',default='equatorial', help="Coordinate system, can be equatorial or galactic")
    parser.add_argument('-equinox',default=2000, help="Epoch for coordinates, can be 1950 or 2000")
    parser.add_argument('-gifsize',default=0,help="Size of gifs outputed by previews (not functioning now)")
    args = parser.parse_args()
    d=args.__dict__
    out = d.pop('output')
    res = heasarc(**d)
    if res.vot:
        if out.find('text_table')==0:
            if len(out.split('=')):
                res.pprint_text()
            else:
                fn = out.split('=')[-1]
                res.pprint_text(open(fn,'w'))
        elif out.find('pdf')==0:
            if len(out.split('='))!=2:
                print "Pleace specify name for pdf output like -output pdf=file.pdf"
            else:
                res.pprint_pdf(out.split('=')[-1])
        else:
            print "Check calling sequence"
    else:
        print "Something went terribly wrong! The earth will explode :) Please contribute to the script to make it better!"
 