# Como publicar utilizando apps desenvolvidos em R
# Tutorial - RStudio Desktop e RStudio Server

Tutorial para estagiarios que desenvolvem apps Shiny em Windows e publicam via fluxo PR -> main -> deploy automatico.

## Objetivo

Desenvolver app com seguranca e publicar em:

- `http://shiny.labfsg.intra/<nome-do-app>/`

## Onde trabalhar

- codigo da app: repo `LabFSG-UFSC/shiny-server`
- operacao/infra: repo `capacitacao-operacao`

## Caminho A - RStudio Desktop (Windows)

Use este caminho quando voce desenvolve localmente no seu notebook/desktop.

### 1. Preparar ambiente

1. Instalar `Git for Windows`.
2. Instalar `R`.
3. Instalar `RStudio Desktop`.
4. Clonar repo de apps:

```bash
git clone https://github.com/LabFSG-UFSC/shiny-server.git
cd shiny-server
```

### 2. Criar branch da app

```bash
git checkout main
git pull origin main
git checkout -b app/meu-app
```

### 3. Estrutura da app

```text
apps/meu-app/
  app.R
```

ou

```text
apps/meu-app/
  ui.R
  server.R
```

### 4. Rodar localmente no RStudio Desktop

No RStudio:

- abrir `app.R` (ou `ui.R`/`server.R`)
- clicar `Run App`
- validar comportamento

### 5. Commit e PR

```bash
git add .
git commit -m "feat(app): cria meu-app"
git push -u origin app/meu-app
```

Depois abrir PR para `main` no GitHub.

### 6. Publicacao

Apos aprovacao + merge:

- workflow `Deploy Shiny Apps (main only)` publica automaticamente
- validar URL final:

```bash
curl -I http://shiny.labfsg.intra/meu-app/
```

## Caminho B - RStudio Server (VM)

Use este caminho quando voce desenvolve dentro do RStudio Server da infraestrutura.

### 1. Acesso

- entrar no RStudio Server da VM pelo link interno http://labfsg.intra/rstudio/
- abrir terminal do RStudio Server

### 2. Clone/atualize repo de apps

```bash
git clone https://github.com/LabFSG-UFSC/shiny-server.git
cd shiny-server
```

Se ja existir:

```bash
cd shiny-server
git checkout main
git pull origin main
```

### 3. Branch + desenvolvimento

```bash
git checkout -b app/meu-app
```

Criar app em `apps/meu-app/` e testar no proprio RStudio Server (`Run App`).

### 4. Commit + push + PR

```bash
git add .
git commit -m "feat(app): cria meu-app"
git push -u origin app/meu-app
```

Abrir PR para `main`.

### 5. Publicacao

Depois do merge, o deploy e automatico.

## Regras de seguranca (obrigatorias)

Como o repo de apps e publico:

- nunca subir credenciais, tokens, senhas
- nunca subir dados internos sensiveis
- nunca subir `.env` com segredo real
- preferir dados anonimizados/sinteticos

## Boas praticas de PR

- 1 branch por app ou feature
- commits pequenos e claros
- descrever no PR:
  - objetivo da app
  - rota esperada (`/meu-app/`)
  - dependencias principais
  - evidencias de teste

## Troubleshooting rapido

1. Deploy falhou no GitHub Actions:
- abrir o run e ver etapa de erro
- confirmar estrutura `apps/<nome>/`

2. URL retorna 404:
- confirmar merge na `main`
- confirmar run com `success`
- validar nome da pasta da app

3. App abre com erro:
- revisar logs da app
- revisar dependencias R

## Referencias

- `docs/wiki/Estagiarios-Shiny.md`
- `docs/wiki/Shiny-Server.md`
- `servidor/docs/acesso/SHINY_SERVER_CICD_MAIN_ONLY.md`
