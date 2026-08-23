# In der Ausbildung wurde nur python:3 angegeben, besser ist es die ganze version anzugeben.
FROM python:3.12-slim

WORKDIR /usr/src/app

# COPY kopiert die angegebenen files. 
# Hier mit "./" in das angegebene workdir: /usr/src/app
COPY requirements.txt ./

# Mit RUN normale Befehle (hier Linux) ausführen.
# Hier ist der absolute Pfad angegeben, würde wahrscheinlich auch nur mit
# pip install funktionieren

# Hier wird pip installiert
RUN /usr/local/bin/python -m pip install --upgrade pip
# Hier wird die requirements installiert mit no cache (empfohlen von docker).
RUN pip install --no-cache-dir -r requirements.txt

# Hier wird angegeben dass wir alles vom Arbeitsfolder (oben) in unsere virtuelle Maschine kopieren wollen.
COPY . .


# Hier mit CMD werden am ende alle nötigen Befehle ausgeführt um alles nacheinander zu starten.
# Es wird absichtlich am Ende nicht der localhost genomen, da wir ja eine weiterleitung zu unserer Maschine machen möchten damit alles online ist.
# Das macht man mit dem 0.0.0.0:8000
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

# Am Ende noch das file builden mit:
# docker build --tag <name> .

# das --tag benennt das file
# der punkt am ende sagt dass es im folder gebuildet wird (noch mehr infos)

# Nach dem build alles starten
# docker run --publish 8000:8000 coderrtest
# Port 8000:8000 leitet den Port von der linuxmachine zu der windowsmachine weiter.

# Um codeänderungen im Image gleich umzuschreiben ohne immer manuell bauen zu müssen,
# kann man den folder/code mounten.
# docker run —publish 8000:8000 -it -v “C:/dev/testapp/src/app:/usr/src/app” coderrtest