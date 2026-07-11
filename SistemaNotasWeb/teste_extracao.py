from utils_pdf import ler_pdf

dados = ler_pdf("nota.pdf")

print("\n===== DADOS EXTRAÍDOS =====\n")

for campo, valor in dados.items():
    print(f"{campo}: {valor}")

print("\n===== TEXTO COMPLETO DO PDF =====\n")
print(dados["texto"])