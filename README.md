# Verificador de Imagens Repetidas

Um programa Python completo com interface gráfica para gerenciar imagens.

## 🎯 Funcionalidades

### 🔍 Procurador de Imagens Repetidas
- **MD5 Hashing** - Detecta duplicatas exatas (byte-por-byte)
- **Perceptual Hashing (phash)** - Encontra imagens similares mesmo com redimensionamentos
- **Análise de Metadados** - Resolução, tamanho, data de captura EXIF
- **Preview Side-a-Lado** - Compare até 3 imagens simultaneamente
- **Delete Rápido** - Clique no ✕ vermelho para marcar eliminação
- **Caminho Completo** - Veja o caminho de cada ficheiro para decisões informadas
- **Cache Automático** - Rescans são instantâneos

### 📅 Editor de Data de Fotos (NOVO!)
- **Modificar Data EXIF** - Altere data de captura facilmente
- **Múltiplos Formatos** - Suporta YYYY, YYYY:MM:DD, DD/MM/YYYY, etc
- **Edição em Lote** - Atualize várias fotos de uma vez
- **Pré-visualização** - Veja cada foto antes de salvar
- **Ideal para Digitalizações** - Perfeito para fotos digitalizadas sem data

### ⚙️ Menu Principal
- Escolha entre funcionalidades (Duplicatas ou Datas)
- Interface limpa e intuitiva

## 📦 Instalação

### 1. Requisitos
- Python 3.8+
- pip

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 🚀 Como Usar

### Opção 1: Menu (Recomendado)
```bash
python main.py
```
Aparece um menu para escolher entre:
- 🔍 Procurador de Imagens Repetidas
- 📅 Editor de Data de Fotos

### Opção 2: Modo Direto
```bash
python main.py duplicates    # Abrir procurador
python main.py exif          # Abrir editor de datas
```

---

## 🔍 Procurador de Imagens Repetidas

### Passo a Passo

**1. Selecionar Pasta**
```
Clique em "📁 Selecionar Pasta"
```

**2. Escanear**
```
Clique em "🔍 Escanear"
Aguarde enquanto o programa processa as imagens
```

**3. Visualizar Duplicatas**
```
Navegue com "⬅ Anterior" / "Próximo ➡"
Cada grupo mostra:
  • % de similaridade
  • Resolução e tamanho
  • Data de captura
  • Caminho completo
```

**4. Marcar para Eliminação**
```
Clique no "✕" vermelho no canto superior direito
(fica destacado quando marcado)
```

**5. Eliminar**
```
Clique em "🗑 Eliminar Marcadas (🔴)"
Confirme a ação (irreversível!)
```

---

## 📅 Editor de Data de Fotos

### Como Usar

**1. Selecionar Fotos**
```
📁 Selecionar Pasta com Fotos (escaneia recursivamente)
ou
➕ Adicionar Ficheiros (escolhe ficheiros específicos)
```

**2. Navegar**
```
⬅ Anterior / Próximo ➡
```

**3. Definir Data**
```
Digite a data no formato preferido:
  • YYYY (apenas ano) → 2004
  • YYYY:MM:DD → 2004:12:25
  • DD/MM/YYYY → 25/12/2004
  • YYYY:MM:DD HH:MM:SS → 2004:12:25 14:30:00
```

**4. Guardar**
```
✓ Guardar Data (foto atual)
✓ Guardar Tudo (todas as fotos com a mesma data)
```

---

## 📁 Estrutura do Projeto

```
Verificador de Imagens Repetidas/
├── main.py              # Entry point com menu
├── gui.py              # Interface procurador (GUI Tkinter)
├── exif_editor.py      # Editor de datas EXIF
├── menu_screen.py      # Menu principal
├── image_scanner.py    # Lógica de scanning/hashing
├── requirements.txt    # Dependências
└── README.md          # Este ficheiro
```

## 🔧 Detecção de Duplicatas

### Duplicatas Exatas
- **MD5 idêntico** = mesma imagem byte-por-byte
- Detectadas instantaneamente

### Duplicatas Similares
- **Perceptual Hash (phash)** compara conteúdo visual
- **Threshold: 85%** de similaridade
- Detecta: redimensionamentos, compressões, ligeiras edições

### Metadados Comparados
- Resolução (largura × altura)
- Tamanho ficheiro
- Data de modificação
- Data EXIF (se disponível)

## ⚡ Otimizações

- **Cache** em `.image_cache.json` para rescans rápidos
- **Multi-threading** - UI não bloqueia durante scanning
- **Previews Redimensionadas** - economia de memória
- **Primeira execução**: ~1-2 min (192 imagens)
- **Rescans**: instantâneos (usando cache)

## 🎨 Interface

### Procurador de Duplicatas
```
┌─ Grupo 1/5 | Tipo: similar | Similaridade: 92% ─────────────┐
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │              │  │              │  │              │       │
│  │   Imagem 1   │  │   Imagem 2   │  │   Imagem 3   │       │
│  │  ✕ (canto)   │  │  ✕ (canto)   │  │  ✕ (canto)   │       │
│  │              │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  📁 /caminho/img1  📁 /caminho/img2  📁 /caminho/img3       │
│  📏 1920x1080      📏 1920x1080      📏 1920x1080           │
│  💾 2.3 MB         💾 2.3 MB         💾 2.3 MB              │
└───────────────────────────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Scanning Lento
- Primeira vez é normal (cálculos de hash)
- Próximas buscas usam cache (muito rápido)
- Pastas com 1000+ imagens: alguns minutos

### Algumas Imagens Não Aparecem
- Formatos não suportados são ignorados
- Permissões insuficientes
- Ficheiros corrompidos (são pulados com log)

## 📋 Formatos Suportados

✅ JPG / JPEG
✅ PNG
✅ GIF
✅ BMP
✅ WebP
✅ TIFF

## 💡 Ideias Futuras

Veja [IDEIAS_FUTURAS.md](IDEIAS_FUTURAS.md) para features planeadas:
- Redimensionar fotos em lote
- Renomear com padrões customizáveis
- Converter formatos (JPG ↔ PNG, etc)
- Organizar por data automaticamente
- Integração com cloud storage
- Interface web

## 🛠️ Tecnologias

- **Python 3.8+**
- **Pillow** - Processamento de imagens
- **imagehash** - Perceptual hashing
- **OpenCV** - Visão computacional
- **Tkinter** - Interface gráfica

## 📄 Licença

Livre para uso pessoal e comercial.

## 🧪 Log de Testes

Durante a execução, a aplicação grava um log persistente em:

```text
logs/app.log
```

Esse ficheiro regista arranque, modo selecionado e erros não tratados. É o primeiro sítio a verificar quando algo falhar num teste.

## 🌐 GitHub Pages

Este projeto já fica preparado para publicar uma página estática em GitHub Pages através da pasta `docs/` e do workflow em `.github/workflows/pages.yml`.

Depois de criar o repositório no GitHub, basta ativar Pages para publicar a landing page do projeto.

---

**Desenvolvido com ❤️ em Python**
