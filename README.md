# 🌳 Forest Inventory Automation

Sistema para **padronização inteligente de dados de inventário florestal**, com foco em identificação e correção automática de nomes de espécies.

---

## 🧠 Sobre o projeto

Este projeto surgiu da necessidade real de tratar planilhas de inventário florestal que chegam com:

* nomes incompletos (`p. terra`)
* variações de escrita (`pau terra`, `pau-terra`)
* erros ortográficos
* inconsistência na padronização

O sistema resolve isso aplicando técnicas de:

* **normalização textual**
* **fuzzy matching (matching aproximado)**
* **enriquecimento de dados**
* **correção assistida pelo usuário**

---

## ⚙️ Funcionalidades

### 🔎 Padronização automática

* Identifica nomes comuns de espécies mesmo com erros ou abreviações
* Converte para formato padronizado (ex: `Pau-terra`)
* Retorna também o **nome científico**

---

### 🤖 Matching inteligente

* Uso de similaridade de texto (RapidFuzz)
* Score de confiança para cada correspondência
* Tratamento de casos ambíguos

---

### 🧹 Normalização de dados

* Remoção de acentos
* Padronização de caixa (lowercase)
* Limpeza de caracteres especiais

---

### ✍️ Correção manual assistida

* Exibe espécies não reconhecidas
* Permite correção direto na interface
* Atualiza os dados em tempo real

---

### 🧠 Sistema adaptativo (em evolução)

* Possibilidade de armazenar correções
* Aprendizado progressivo com uso real

---

## 🏗️ Estrutura do projeto

```
forest-inventory-automation/
│
├── app/
│   └── main.py                # Interface Streamlit
│
├── services/
│   └── excel_service.py      # Processamento de planilhas
│
├── species/
│   ├── base.py               # Base de espécies
│   ├── matcher.py            # Lógica de matching
│   └── normalizer.py         # Normalização de texto
│
├── formatter.py              # Formatação de saída
│
└── requirements.txt
```

---

## 📊 Fluxo do sistema

1. Upload da planilha
2. Leitura dos dados
3. Normalização dos nomes
4. Matching com base de espécies
5. Classificação por score
6. Correção manual (se necessário)
7. Exportação da planilha tratada

---

## 🧪 Exemplo

| Entrada     | Saída (Comum) | Saída (Científico)      |
| ----------- | ------------- | ----------------------- |
| p. terra    | Pau-terra     | Qualea grandiflora      |
| angico      | Angico        | Anadenanthera colubrina |
| ipe amarelo | Ipê-amarelo   | Handroanthus albus      |

---

## 🚀 Tecnologias utilizadas

* Python
* Pandas
* Streamlit
* RapidFuzz

---

## ▶️ Como rodar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/forest-inventory-automation.git
cd forest-inventory-automation
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

```bash
streamlit run app/main.py
```

---

##
