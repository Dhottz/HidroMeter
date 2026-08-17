# Requisitos

## Requisitos funcionais

### Autenticação e acesso (Entrega 1)
- RF01: Usuário deve poder se autenticar (login) com email/senha.
- RF02: Sistema deve diferenciar dois papéis: síndico e morador.
- RF03: Síndico só acessa dados do(s) condomínio(s) ao(s) qual(is) está vinculado.
- RF04: Morador só acessa dados da(s) unidade(s) à(s) qual(is) está vinculado.

### Cadastro (Entrega 1)
- RF05: Síndico pode cadastrar/editar/remover blocos, unidades e hidrômetros do seu condomínio.
- RF06: Sistema deve listar unidades filtradas pelo papel do usuário logado.

### Leituras (Entrega 2)
- RF07: Sistema deve ingerir leituras de hidrômetro (timestamp + litros acumulados).
- RF08: Sistema deve calcular vazão instantânea a partir da diferença entre leituras consecutivas.
- RF09: Usuário deve visualizar gráfico de consumo por unidade e por período.

### Detecção de vazamento e comparação (Entrega 3)
- RF10: Sistema deve calcular baseline de vazão noturna por unidade (mediana dos últimos 7-14 dias).
- RF11: Sistema deve gerar alerta quando vazão noturna atual ultrapassar o baseline por N noites seguidas.
- RF12: Síndico deve visualizar todos os alertas ativos do condomínio.
- RF13: Morador deve visualizar apenas alertas da própria unidade.
- RF14: Síndico deve visualizar ranking de consumo entre unidades do condomínio.

### Previsão e recomendações (Entrega 4)
- RF15: Sistema deve prever consumo futuro por unidade com base no histórico.
- RF16: Sistema deve gerar recomendações de economia baseadas em regras (ex: consumo X% acima da média do prédio).

## Requisitos não funcionais

- RNF01: Senhas armazenadas com hash (bcrypt), nunca em texto puro.
- RNF02: Autenticação via JWT, expiração configurável.
- RNF03: Schema do banco versionado via Prisma migrations.
- RNF04: Simulador deve gerar dataset reprodutível (seed fixa) para permitir testes consistentes.
- RNF05: API deve responder listagens paginadas quando o volume de dados justificar (ex: leituras).

## Fora de escopo (v1)

- Notificação por push/email/SMS de alertas (pode ser mencionado como evolução futura).
- Cobrança/faturamento de água.
- Hardware físico real (sensores simulados nesta fase).
