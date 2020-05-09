from heapq import nlargest
import subprocess
import textract
import regex as re
import spacy
import difflib
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation

nature_to_count = ['NOUN','VERB','ADJ','ADV']
nlp = spacy.load('fr_core_news_md')
word_frequencies = {}
stopwords = list(STOP_WORDS)

class PDFExtractor:
    def __init__(self, UnNomPdf):
        self.pdf = UnNomPdf

    def getTextFromPDF(self):
        '''
            nouveau nom pour getText
        '''
        text = textract.process(self.pdf, encoding='utf-8')
        text = str(text, "utf-8")
        text = text.replace("  \n  ",'\n')
        return text

    def getSubtitlesFromTableContent(self,text):
        '''
            nouveau nom pour getSubtitles
        '''
        toc = subprocess.check_output(
            "mutool show "+self.pdf+" outline", shell=True)
        toc = str(toc, "utf-8")
        subtitles = []
        if len(toc) > 10:
            temp_list = toc.split("\n")
            for e in temp_list:
                temps = e.split("#")
                name = (str.strip(temps[0]))
                if(len(temps) > 1):
                    #page = (temps[1].split(","))[0]
                    subtitles.append(name)
        else:
            tbm_temp = text.split(".......")
            if len(tbm_temp) > 0:
                first_ele = tbm_temp[0].split('\n')
                tbm_temp[0] = first_ele[len(first_ele)-1]
                #last_ele = (tbm_temp[len(tbm_temp)-1].split('\n'))[0]
                i = 1
                while i < len(tbm_temp)-1:
                    if len(tbm_temp[i].split('\n')) > 1:
                        ele = (tbm_temp[i].split('\n'))[1]
                        subtitles.append(ele.strip())
                    i += 1
        return subtitles

class SummaryMaker:
    def __init__(self, UnNomPdf):
        self.filename = UnNomPdf
        self.all_text = ""
        self.titles = []
        self.map_nomParties_contenu = {}
        self.pdfHelper = PDFExtractor(self.filename)
        self.sommaire = ""
        self.dsAnalyser = DSAnalyser()
        self.map_nomParties_motsImportants = {}
    
    def printValue(self):
        key = self.map_nomParties_contenu.keys()
        i = 0
        for k in key:
            if i<20:
                print(f"une key : {k}" )
                print(self.map_nomParties_contenu[k])
                print("")
                i=i+1

    def string_similar(self, s1, s2):
        return difflib.SequenceMatcher(None, s1, s2).quick_ratio()

    def getParties(self): 
        '''
            nouveau nom de getParagraphes()
        '''
        if len(self.titles)>1:   
            i = 0
            paragraphes = {}
            while i < len(self.titles)-1:
                pattern = self.titles[i]+'\n(.*?)'+self.titles[i+1]
                if self.all_text:
                    res=re.findall(pattern,self.all_text,re.S)
                    if len(res)>0:
                        paragraphes[self.titles[i]]=res[0]
                    else:
                        paragraphes[self.titles[i]]=''
                    i+=1
        
        return paragraphes

    def organizePoly(self):
        ''' 
        1. self.all_text = pdfHelper.getTextFromPDF()
        2. self.titles = pdfHelper.getSubtitlesFromTableContent(text)
        3. self.map_nomParties_contenu = getParties()
        '''
        self.all_text = self.pdfHelper.getTextFromPDF()
        self.titles = self.pdfHelper.getSubtitlesFromTableContent(self.all_text)
        self.map_nomParties_contenu = self.getParties()

        # Obtenir sommaire
        if "Sommaire" in self.titles:
            self.sommaire = self.map_nomParties_contenu["Sommaire"]
        elif "Table des matières" in self.titles:
            self.sommaire = self.map_nomParties_contenu["Table des matières"]
        else:
            self.sommaire = "vide"
        
        # Nettoyer les clés 
        key = self.map_nomParties_contenu.keys()
        keys_to_remove = []
        for k in key:
            if not self.map_nomParties_contenu[k] and not k in self.sommaire:
                keys_to_remove.append(k)
        for k in keys_to_remove:
            del self.map_nomParties_contenu[k]
    
    def addNewDS(self, DSs):
        '''
            for ds in DSs:
                self.dsAnalyser.add_ds_name(ds)
            self.dsAnalyser.analyseDSImportantWords()
        '''
        for ds in DSs:
            self.dsAnalyser.add_ds_name(ds)
        self.dsAnalyser.analyseDSImportantWords()

    def summarisePartie(self,nomPartie):
        '''
        analyseSimple avec text = self.map_nomParties_contenu(nomPartie)
        '''
        important_words_subtitle = nomPartie.split(' ')
        for w in important_words_subtitle:
            w = w.lower()

        text = self.map_nomParties_contenu[nomPartie]

        if not text:
            self.map_nomParties_motsImportants[nomPartie] = []
            return

        docx = nlp(text)
        """# WORD FREQUENCY TABLE"""
        # Build Word Frequency
        # word.text is tokenization in spacy
        word_frequencies = {}
        for word in docx:
            if (word.pos_ in nature_to_count) and (not (word.is_stop)) and (word.lemma_ not in stopwords):
                if word.lemma_ not in word_frequencies.keys():
                    word_frequencies[word.lemma_] = 1
                else:
                    word_frequencies[word.lemma_] += 1

        """# MAXIMUM WORD FREQUENCY"""
        # Maximum Word Frequency
        maximum_frequency = max(word_frequencies.values())
        # Calculate the coefficent of word frequence
        for word in word_frequencies.keys():  
            word_frequencies[word] = (word_frequencies[word]/maximum_frequency)
        
        """# GET Liste des mots clés"""
        word_tmp = word_frequencies
        maxWord = 5
        if len(word_frequencies) < 5:
            maxWord = len(word_frequencies)

        list_mots_cles = []
        if maxWord > 0:
            for i in range(maxWord):
                MostUseful_Score = 0
                MostUseful = ""
                for w in word_tmp.keys():
                    if word_tmp[w] > MostUseful_Score:
                        MostUseful_Score = word_tmp[w]
                        MostUseful = w
                # ici on a trouvé le max actuel:
                list_mots_cles.append(MostUseful)
                del word_tmp[MostUseful]
        
        self.map_nomParties_motsImportants[nomPartie] = list_mots_cles

        """# SENTENCE SCORE AND RANKING OF WORDS IN EACH SENTENCE"""
        # Sentence Tokens
        sentence_list = [ sentence for sentence in docx.sents ]
        important_words_ds = self.dsAnalyser.important_words
        important_words_ds_token = self.dsAnalyser.important_words_token
        # Sentence Score via comparrng each word with sentence
        sentence_scores = {}
        for sent in sentence_list:  
            for word in sent:
                bonus = 0
                if  (word.lemma_.lower() in word_frequencies.keys()):
                    
                    for w in important_words_ds_token:
                        if self.string_similar(w.lemma_.lower(),word.lemma_.lower())>0.85 or w.similarity(word)>0.85:
                            bonus += 5 
                            break

                    for w in important_words_subtitle:
                        if self.string_similar(w,word.lemma_.lower())>0.85:
                            bonus += 5
                            break

                    if len(sent.text.split(' ')) < 30:
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word.lemma_.lower()]+bonus
                        else:
                            sentence_scores[sent] += (word_frequencies[word.lemma_.lower()]+bonus)

        """# FINDING TOP N SENTENCE WITH LARGEST SCORE"""
        len_text = int(len(sentence_list)/4)
        summarized_sentences = nlargest(len_text, sentence_scores, key=sentence_scores.get)
        # Convert Sentences from Spacy Span to Strings for joining entire sentence
        '''
        for w in summarized_sentences:
            print(w.text)
        '''

        # List Comprehension of Sentences Converted From Spacy.span to strings
        final_sentences = [ w.text for w in summarized_sentences ]
        final_sentences = map(str.strip, final_sentences)
        return final_sentences
        '''
        """# Join sentences"""
        summary = ' '.join(final_sentences)
        return summary
        '''
class DSAnalyser:

    def __init__(self):
        self.ds = []
        self.important_words = []
        self.important_words_token = []

    def add_ds_name(self, nameDS):
        '''
            ajoute un nom de fichier ds dans la liste self.ds
        '''
        self.ds.append(nameDS)

    def analyseDSImportantWords(self):
        '''
            for ds in self.ds :
                self.add_ds_importantWords(ds)
        '''
        for ds in self.ds :
            self.add_ds_importantWords(ds)
        

    def add_ds_importantWords(self, nameDS):
        '''
            nouveau nom pour analyse_ds
            ajoute les mots important du fichier nameDS à l'objet self.important_words
        '''
        question_list=[]
        text1 = textract.process(nameDS)
        u = str(text1, "utf-8")
        docx = nlp(u)
        sentence_list = [ sentence for sentence in docx.sents ]
        for s in sentence_list:
            if s[-1].text=='?' or s[-2].text=='?':
                question_list.append(s)
        this_important_words=[]
        this_important_words_token=[]
        for q in question_list:
            for word in q:
                if (word.pos_ in nature_to_count) and (not (word.is_stop)) and (word.lemma_ not in stopwords):
                    this_important_words.append(word.lemma_)
                    this_important_words_token.append(word)

        if not this_important_words:
            print("pas de mots importants pour le ds")
        else:
            if self.important_words: 
                for i in this_important_words:
                    # Si le mot n'est pas déjà présent
                    if i not in self.important_words.append(i):
                        self.important_words.append(i)
            else:
                for i in this_important_words:
                    self.important_words.append(i)
        

        if  this_important_words_token:
            if self.important_words_token: 
                for i in this_important_words_token:
                    # Si le mot n'est pas déjà présent
                    if i not in self.important_words_token.append(i):
                        self.important_words_token.append(i)
            else:
                for i in this_important_words_token:
                    self.important_words_token.append(i)


