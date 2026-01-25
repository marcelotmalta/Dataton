# Contribuindo

Obrigado por contribuir! Siga estes passos:

1. Fork do repositório.
2. Crie uma branch com nome descritivo: `feat/nome-curto` ou `fix/descricao`.
3. Implemente com pequenos commits, seguindo o padrão de mensagens (ex.: `feat: adicionar preprocessor`).
4. Rode linter e testes:
   ```
   make install
   make test
   ```
5. Abra PR apontando para `develop` (ou branch principal definida), preencha o template de PR.
6. Aguarde revisão — responda comentários e atualize o PR quando solicitado.

Regras adicionais:
- Use o estilo de código definido no repositório (PEP8/black/isort sugeridos).
- Mantenha PRs pequenos e focados.
- Verifique obrigatoriamente questões de privacidade e LGPD: não inclua dados pessoais identificáveis sem autorização. Se estiver trabalhand o dataset, garanta que apenas dados anonimizados sejam subidos e documente o processo de anonimização.

Processo de revisão:
- 2 revisores aprovando para merge em `main`.
- CI deve passar (testes + linter).

