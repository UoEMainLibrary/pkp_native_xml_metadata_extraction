# OJS Native XML extraction scripts

This repository contains various Python scripts for extracting metadata from OJS's Native XML export file and putting it into more usable formats for journal editors. These scripts were designed against Edinburgh Diamond's OJS instances.

Edinburgh Diamond, situated within Edinburgh University Library, offers free publishing services to support Diamond Open Access books and journals created by University of Edinburgh academics and students. https://library.ed.ac.uk/research-support/edinburgh-diamond

Edinburgh University Library offers a journal and book hosting service to members of the Scottish Confederation of University & Research Libraries (SCURL), as well as external organisations. https://library.ed.ac.uk/research-support/open-hosting-service. 

## convert_ojs_xml.py

convert_ojs_xml.py converts OJS Native XML into CSV format. It's basically the inverse of https://github.com/UoEMainLibrary/pkp_import (forked from https://github.com/ualbertalib/ojsxml) which converts a CSV file to OJS Native XML.

### usage

`python3 convert_ojs_xml.py --input_xml FILENAME.xml --output_csv FILENAME.csv`

or

`docker compose run --rm convert_ojs_xml`

## extract_ojs_pdfs.py

extract_ojs_pdfs.py extracts the base64-encoded PDF data from the OJS Native XML file and saves separate PDF files in a single directory with filenames based on author surname and volume / issue data.

### usage

`python3 extract_ojs_pdfs.py --input_xml FILENAME.xml --output_dir ./pdfs`

or

`docker compose run --rm extract_ojs_pdfs`