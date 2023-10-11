import urllib
import warnings
from pathlib import Path as p

import pandas as pd
import re
from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter



class IRetrive:
  def __init__(self, filepath):
    loader = PyPDFLoader(filepath)
    pages = loader.load_and_split()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    context = "\n\n".join(str(p.page_content) for p in pages)
    texts = text_splitter.split_text(context)
    st=""
    for i in texts:
      st += i

    sents = st.split("\n")
    import re
    pattern = r'land\s*\(\s*Address\s*,\s*plan\s*details\s*and\s*title\s*reference\s*\)'
    extracted_text=[]

# The string to search in (including variations)
    input_string = st  # Replace 'st' with your actual input string

    # Use re.search with re.DOTALL flag to find a match across multiple lines
    match = re.search(pattern, input_string, re.DOTALL | re.IGNORECASE)

    if match:
        # Find the starting index of the match
        # Find the line number where the match starts
        start_line = input_string.count('\n', 0, match.start()) + 1  # Add 1 to convert from 0-based index

        # Split the input string into lines
        lines = input_string.split('\n')

        # Extract the two lines after the match
        extracted_lines = lines[start_line + 1 : start_line + 3]  # Extract lines 2 and 3 after the match

        if extracted_lines:

            # Create a string to store the extracted lines
            extracted_text = "\n".join([line.strip() for line in extracted_lines])
            first_digit_index = re.search(r'\d', extracted_text)

            if first_digit_index:
                # Trim the text to keep everything after the first digit
                extracted_text = extracted_text[first_digit_index.start():]

    keys = ['vendor  ','date for completion', 'land (address', 'plan details and', 'VACANT POSSESSION','purchaser’s solicitor    ','improvements','inclusions ','exclusions','Land tax']
    self.st=st
    dc={}
    for item in keys:
      for i,x in enumerate(sents):
        if item in x:
          dc[item] = [sents[i], sents[i+1], sents[i+2], sents[i+3],sents[i+4]]
        else:
          dc[item]=" "
    pattern_v = re.compile(r'\bvendor\b\s+([\w\s]+)', re.IGNORECASE)
    matches_v = pattern_v.findall(st)
    pattern_b = re.compile(r'\bbalance\b\s*(\$[\d,.]+)')
    matches_b = pattern_b.findall(st)
    dc['purchaser’s solicitor    ']=matches_b
    dc['vendor  '] = matches_v[0].split('\n')
    dc[keys[1]] = dc[keys[1]][0] #date of completion
    # print(dc['VACANT POSSESSION'])
    # dc['VACANT POSSESSION'] = dc['VACANT POSSESSION'][:-2]
    #dc[keys[5]] = dc[keys[5]][-2]
    dc['improvements'] = dc['improvements'][0:2]
    dc['land (address']=extracted_text
    dc['exclusions']=dc['exclusions'][0]

    dc['Land tax']=dc['Land tax'][0]


    self.dc = dc


  def getName(self):
      pattern = re.compile(r'\bvendor\b\s+([\w\s]+)', re.IGNORECASE)
      matches = pattern.findall(self.st)
      vendor = matches[0].split('\n')
      if len(vendor) > 1:
        return vendor[0]
      else:
        return "Error"

  def getLandaddress(self):
    return self.dc['land (address'].split("\n")[0]

  def getPlandetails(self):
    return self.dc['land (address'].split("\n")[1]
  def getSettlementdate(self):
    doc = self.dc['date for completion'].split('(',1)
    if len(doc) == 0:
      return "Need to be confirmed"
    return doc

  def getLandstatus(self):
    sts = re.findall(r'\uf0fe\s*([^☐\uf0fe]+)', self.dc['VACANT POSSESSION'][0])
    if len(sts) == 0:
      return "Further clarification is also required of whether the Vendor will be able to provide vacant possession on settlement."
    return sts

  def getPrice(self):
    pattern = re.compile(r'\bbalance\b\s*(\$[\d,.]+)')
    matches = pattern.findall(self.st)
    print(matches)
    #price = dc['purchaser’s solicitor    '].split('balance')[1].strip()
    if len(matches) == 0:
      return "TBA"
    return matches[0]

  def getImprovments(self):

    selected_options = re.findall(r'\uf0fe\s*([^☐\uf0fe]+)', self.dc['improvements'][0])

    if len(selected_options) == 0:
      return "Need to be confirmed"
    elif len(selected_options) == 1:
      return selected_options[0]
    else:
      impvs = ""
      for i in range(0, len(selected_options)-1):
        impvs += selected_options[i] + ','
      impvs += 'and' + selected_options[-1]
      return impvs

  def getInclusions(self):
    inc = re.findall(r'\uf0fe\s*([^☐\uf0fe]+)', self.dc['inclusions '][0])

    if len(inc) != 0:
      return "Inclusions are marked under the inclusion tab of the contract"
    return "Inclusions are not marked under the inclusion tab of the contract"

  def getExclusions(self):
    exc = self.dc['exclusions'].split('exclusions')[-1]
    return exc

  def getLandtax(self):
    ltx = re.findall(r'\uf0fe\s*([^☐\uf0fe]+)', self.dc['Land tax'])
    if len(ltx) == 0:
      return "Land tax is not marked as adjustable or not adjustable"
    elif ltx[0].strip().lower() == 'no':
      return "Land tax is marked as not adjustable"
    else:
      return "Land tax is marked as adjustable"
