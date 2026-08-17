# Decisões técnicas

Registro curto de decisões relevantes e o porquê (estilo ADR simplificado).

## 1. Vazão instantânea é campo derivado, não bruto

Sensores de pulso (1 pulso = 1 litro) só emitem contagem cumulativa — o datalogger/gateway transmite periodicamente o contador acumulado (`litros_acumulados`, tipo odômetro, nunca zera). A vazão instantânea não existe como dado bruto do sensor nesse tipo de arquitetura; ela é calculada:

```
vazao = (litros_acumulados_atual - litros_acumulados_anterior) / tempo_decorrido
```

Decisão: calcular e persistir `vazao_instantanea` no momento da ingestão (por performance de leitura), mas documentar que é derivada — importante pra não passar a impressão de que o hardware simulado tem um sensor de vazão dedicado (ele não tem, no cenário de pulso puro).

## 2. Granularidade de leitura: horária (default)

Dispositivos LPWAN reais (LoRaWAN, NB-IoT) tipicamente transmitem a cada 15min-1h para economizar bateria — não é contínuo. Escolhido 1 leitura/hora como default: dá granularidade suficiente pra detecção MNF (janela noturna de várias horas) sem gerar volume de dados desnecessário (90 dias × 24h × ~150 unidades ≈ 324 mil linhas). Fácil de reduzir para 15min no simulador se for preciso mais resolução.

## 3. Detecção de vazamento: baseline adaptativo por unidade (MNF)

Ver `plano-projeto-hidrometro.md`. Escolhido baseline adaptativo (mediana da vazão noturna dos últimos 7-14 dias por unidade) em vez de threshold fixo global, porque reduz falso positivo em unidades com padrão noturno legítimo diferente da média (ex: irrigação automática). É a mesma abordagem usada por sistemas AMI reais (Minimum Night Flow).

## 4. Multi-tenancy via tabelas de junção N:N

`usuario_condominios` e `usuario_unidades` em vez de FK direta em `usuarios`, porque no mundo real um síndico pode administrar mais de um condomínio e um morador pode ter mais de uma unidade. Evita reescrever o schema quando esse caso aparecer.

## 5. Dataset simulado gerado de uma vez (não em tempo real)

Para ter volume de dados suficiente para análise/previsão desde já, sem depender de um processo rodando por semanas. O simulador gera 3 meses de histórico numa única execução, com seed fixa para reprodutibilidade (RNF04).
