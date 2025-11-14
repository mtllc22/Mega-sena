# 🎰 Automação Mega-Sena – Python + Selenium

Este projeto realiza a **automação completa** do envio de jogos da Mega-Sena diretamente no site das Loterias Caixa, utilizando **Python, Selenium e uma planilha Excel** como fonte de dados.
O sistema é totalmente automatizado, inclui **logs**, **prints**, **relatório final em CSV**, e **detecção de jogos repetidos**.

---

## 📌 Funcionalidades

### 📝 Leitura da Planilha

* Lê o arquivo `mega.xlsx` (aba `mega`)
* Extrai e valida as dezenas de cada jogo
* Ordena e padroniza os números

### 🌐 Automação Web com Selenium

O robô faz automaticamente:

* Abertura do Chrome
* Navegação até o site da Caixa
* Fechamento de popups
* Marcação das dezenas no volante
* Envio do jogo ao carrinho
* Tratamento de erros e retentativas por elemento

### 🧠 Detecção de Jogos Repetidos

* Mantém um `set()` com todos os jogos enviados
* Jogo duplicado = não enviado e registrado no relatório

### 🪵 Sistema de Log

Tudo é registrado em `/logs/`:

* Ações realizadas
* Tentativas de clique
* Erros e exceções
* Sucesso ou falha do envio

### 📸 Prints Automáticos

O script tira screenshots automaticamente em momentos chave:

* Antes de marcar o jogo
* Depois de marcar
* Após enviar ao carrinho
* Em caso de erro

Salvos em `/prints/`.

### 📊 Relatório Final (CSV)

Gerado em `/relatorios/`, contendo:

* Número do jogo
* Dezenas
* Status (`OK`, `ERRO`, `REPETIDO`)
* Caminho do print
* Observações

---

## 📁 Estrutura de Arquivos

```
/logs
   mega_2025-11-14_16-30-22.log

/prints
   antes_jogo_1_1699982221.png
   marcado_jogo_1_1699982223.png
   enviado_1_1699982225.png

/relatorios
   mega_resultados_2025-11-14_16-30-22.csv

script.py
mega.xlsx
```

---

## 🛠 Tecnologias Utilizadas

* Python 3
* Selenium WebDriver
* WebDriver Manager
* OpenPyXL
* CSV
* ChromeDriver

---

## 📦 Instalação

### 1. Clone o repositório:

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPO.git
cd SEU_REPO
```

### 2. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instale as dependências:

```bash
pip install -r requirements.txt
```

**requirements.txt recomendado:**

```
selenium
webdriver_manager
openpyxl
```

---

## 📂 Arquivo mega.xlsx

A planilha deve ter este formato:

| Nome | D1 | D2 | D3 | D4 | D5 | D6 |
| ---- | -- | -- | -- | -- | -- | -- |
| João | 01 | 09 | 22 | 33 | 44 | 55 |

O script extrai da coluna **D1 a D6**, ignorando valores vazios.

---

## ▶️ Execução

```bash
python script.py
```

O Chrome será aberto e o processo iniciará automaticamente.

---

## ⚠️ Avisos

* A automação depende de estabilidade do site da Caixa — falhas podem ocorrer por lentidão ou alterações no layout.
* O script é apenas para fins educacionais. Use com responsabilidade.
* Cada aposta só será finalizada após o pagamento manual no site.

---

## 🧑‍💻 Autor

Rodrigo Dallia
