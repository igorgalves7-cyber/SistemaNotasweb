import fitz

pdf = fitz.open("nota.pdf")

texto = ""

for pagina in pdf:
    texto += pagina.get_text()

print(texto)