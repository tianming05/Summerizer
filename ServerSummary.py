#!/usr/bin/env python3
import http.server
import cgi
import cgitb
import os, sys
import Summarizer
import json

class Server(http.server.CGIHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    def do_HEAD(self):
        self._set_headers()
    def do_POST(self):
        self.cgi_directories = ["/"]
        self._set_headers()
             
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        if "/SummarizeDocument" in self.path:
            self.handleSummarizeDocument(form)
        elif "/upload" in self.path:
            #do nothing
            self.handleUpload(form)
        else:
            self.wfile.write(bytes("No corresponding request", "utf-8"))
    
    def handleSummarizeDocument(self, form):
        pdfName = ""        
        try:
            if form.getvalue("pdfName"):
                pdfName = form.getvalue("pdfName")
        except:
            self.wfile.write(bytes("No object pdfName", "utf-8"))
        
        classSummarizer = Summarizer.SummaryMaker("upload/Cours/"+ pdfName)
        classSummarizer.organizePoly()

        if form["dsNames"].value and not form["dsNames"].value == "null":
            lesDS = form["dsNames"].value
            lesDS = lesDS.split('+')
            lesDS_Path = []
            for d in lesDS:
                lesDS_Path.append("upload/DS/"+d)

            classSummarizer.addNewDS(lesDS_Path)

        '''
        list_json = []
        i = 0

        if form["dsNames"].value:
            if classSummarizer.dsAnalyser.important_words:
                list_json.append({"motsImportantsDS" : classSummarizer.dsAnalyser.important_words})
        else:
            list_json.append({"motsImportantsDS" : ""})

        for partie in classSummarizer.map_nomParties_contenu.keys():
            if(partie == "Sommaire" or partie == "Table des matières"):
                continue
            if i < 5:
                summary = classSummarizer.summarisePartie(partie)  
                l  = []
                # Mots importants
                if classSummarizer.map_nomParties_motsImportants[partie]:
                    l.append({"motsImportants": classSummarizer.map_nomParties_motsImportants[partie]})
                else:
                    l.append({"motsImportants": []})
                # Texte
                if summary:
                    for s in summary:
                        l.append(s)
                else:
                    l.append("")
                d = {partie : l}
                list_json.append(d)
                i=i+1
        '''
        
        list_jsonElement = []
        for partie in classSummarizer.map_nomParties_contenu.keys():
            if(partie == "Sommaire" or partie == "Table des matières"):
                continue
            jsonElement = dict() 
            # Génération du résumé
            summary = classSummarizer.summarisePartie(partie)  
            if summary != "false":
                # titre
                jsonElement["titre"] = partie
                # Mots importants
                l_motsImportants  = []
                if classSummarizer.map_nomParties_motsImportants[partie]:
                    l_motsImportants = (classSummarizer.map_nomParties_motsImportants[partie])
                else:
                    l_motsImportants.append("")

                jsonElement["motsImportants"] = l_motsImportants
                # Texte
                l_ideesCles = []
                if summary:
                    for s in summary:
                        l_ideesCles.append(s)
                else:
                    l_ideesCles.append("")

                jsonElement["ideesCles"] = l_ideesCles

                # Ajouter au list_jsonElement
                list_jsonElement.append(jsonElement)    
            
        self.wfile.write(str(json.dumps(list_jsonElement, ensure_ascii=True)).encode())
    
    def handleUpload(self, form):
        UPLOAD_DIR = './upload/'
        try:
            if form["StoreDS"].value:
                StoreDS = form["StoreDS"].value
        except:
            StoreDS = "false"

        form_file = form["file"]
        if form_file.file:
            fn = os.path.basename(form_file.filename)
            if StoreDS == "true":
                open(UPLOAD_DIR + "DS/" + fn, 'wb').write(form_file.file.read())            
                self.wfile.write(bytes("Completed DS upload", "utf-8"))
            else:
                open(UPLOAD_DIR + "Cours/" + fn, 'wb').write(form_file.file.read())            
                self.wfile.write(bytes("Completed file upload", "utf-8"))

def run(server_class=http.server.HTTPServer, handler_class=Server, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print ('Server running at localhost:8080')
    httpd.serve_forever()        

run()

