import urllib
import warnings
from pathlib import Path as p
import re
import pandas as pd
from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader


class Retrive:
  def __init__(self, filepath):
    loader = PyPDFLoader(filepath)
    pages = loader.load_and_split()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    context = "\n\n".join(str(p.page_content) for p in pages)
    texts = text_splitter.split_text(context)

    st = ""
    for i in texts:
      st += i

    sents = st.split("\n")
    keys = ['vendor  ','date for completion', 'land (address', 'plan details and', 'VACANT POSSESSION','purchaser’s solicitor    ','improvements','inclusions ','exclusions','Land tax']

    dc={}
    for item in keys:
      for i,x in enumerate(sents):
        if item in x:
          dc[item] = [sents[i], sents[i+1], sents[i+2], sents[i+3],sents[i+4]]

    dc[keys[0]] = dc[keys[0]][0] #vendor's name
    dc[keys[1]] = dc[keys[1]][0] #date of completion
    dc['VACANT POSSESSION'] = dc['VACANT POSSESSION'][:-2]
    dc[keys[5]] = dc[keys[5]][-2]
    dc['improvements'] = dc['improvements'][0:2]
    dc['land (address']=dc['land (address'][2:4]
    dc['exclusions']=dc['exclusions'][0]
    dc['Land tax']=dc['Land tax'][0]

    ## Date of completion
    pattern = r'^date for completion (.*)$'
    matches = re.findall(pattern, st, re.MULTILINE)
    for m in matches:
      cleaned_text = re.sub(r'\(clause 15\)', '', m)
      dc[keys[1]] = cleaned_text.strip()

    self.dc = dc


  def getName(self):
    return self.dc['vendor  '].split(' ',1)[1]

  def getLandaddress(self):
    return self.dc['land (address'][0].split(')',1)[1]

  def getPlandetails(self):
    return self.dc['land (address'][1].split(':',1)[-1]

  def getSettlementdate(self):
    doc = self.dc['date for completion']
    if len(doc) == 0:
      return "Need to be confirmed"
    return doc

  def getLandstatus(self):
    sts = re.findall(r'\uf0fe\s*([^☐\uf0fe]+)', self.dc['VACANT POSSESSION'][0])
    if len(sts) == 0:
      return "Further clarification is also required of whether the Vendor will be able to provide vacant possession on settlement."
    return sts[0]

  def getPrice(self):
    price = self.dc['purchaser’s solicitor    '].split('balance')[1].strip()
    if len(price) == 0:
      return "TBA"
    return price

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
    exc = self.dc['exclusions'].split('exclusions')[1]
    return exc

  def getLandtax(self):
    ltx = re.findall(r'\uf0fe\s*([^☐\uf0fe]+)', self.dc['Land tax'])
    if len(ltx) == 0:
      return "Land tax is not marked as adjustable or not adjustable"
    elif ltx[0].strip().lower() == 'no':
      return "Land tax is marked as not adjustable"
    else:
      return "Land tax is marked as adjustable"

import os
def save_uploaded_file(uploaded_file, folder_path):
    with open(os.path.join(folder_path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())


import streamlit as st

import os
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT



import os
import pandas as pd
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL

# ... (previous code)

def main():
    st.title("Information retriever")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        save_uploaded_file(uploaded_file, "Data/")
        pdf_file = os.path.join("Data/", uploaded_file.name)

    question = st.text_input("Hello there! What is your query today?")
    if st.button("Retrieve"):
        if question:
            retriever = Retrive(pdf_file)

            # Create a DataFrame to store the data
            data = {
                "Field": [
                  "Field",
                    "Settlement Date",
                    "Land Status",
                    "Price",
                    "Improvements",
                    "Inclusions",
                    "Exclusions",
                    "Land Tax"
                ],
                "Value": [
                  "Value",
                    retriever.getSettlementdate(),
                    retriever.getLandstatus(),
                    retriever.getPrice(),
                    retriever.getImprovments(),
                    retriever.getInclusions(),
                    retriever.getExclusions(),
                    retriever.getLandtax()
                ]
            }

            df = pd.DataFrame(data)

            # Save data to Excel file
            excel_file = "output.xlsx"
            df.to_excel(excel_file, index=False, header=False)

            # Create a Word document
            doc = Document()
            doc.add_heading("Information Retrieved from PDF", 0)
            doc.add_paragraph("Vendor's Name: " + retriever.getName())
            doc.add_paragraph("Land Address: " + retriever.getLandaddress())
            doc.add_paragraph("Plan Details: " + retriever.getPlandetails())

            # Read the Excel file and add data to the Word document
            df = pd.read_excel(excel_file)
            table = doc.add_table(rows=0, cols=2)
            table.style = 'Table Grid'
            table.alignment = WD_ALIGN_VERTICAL.CENTER

            for index, row in df.iterrows():
                row_cells = table.add_row().cells
                row_cells[0].text = row["Field"]
                row_cells[1].text = str(row["Value"])

            # Save the Word document
            output_docx_file = "output.docx"
            doc.save(output_docx_file)

            # Provide a link to download the generated Word document
            st.markdown(f"**[Download Word Document](/{output_docx_file})**")

if __name__ == "__main__":
    main()
