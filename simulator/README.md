# Simulator

Script que gera o dataset histórico simulado de uma vez (Entrega 2): 1 condomínio, 3 blocos, 50 unidades por bloco, 3 meses de leituras horárias, 10 unidades com vazamento injetado (vazão constante mesmo na janela noturna). Seed fixa para reprodutibilidade (RNF04).

```bash
cd backend && .venv\Scripts\activate     # banco no ar, `alembic upgrade head` e `python seed.py` já executados
python ../simulator/simulate.py          # opções: --dias 90 --seed 42 --fim AAAA-MM-DD
```

- Completa cada bloco do primeiro condomínio até 50 unidades (cada uma com hidrômetro) e **substitui** as leituras desses hidrômetros.
- Usa os models e `calcular_vazao` do backend, então o dado gravado é igual ao da ingestão pela API.
- Escreve `vazamentos_injetados.json` (gabarito: hidrômetro, data de início, L/h), usado para validar a detecção da Entrega 3. Arquivo gerado, fora do git.
- Mesma `--seed` + mesmo `--fim` => mesmo dataset. Sem `--fim`, termina em hoje à 00h.
