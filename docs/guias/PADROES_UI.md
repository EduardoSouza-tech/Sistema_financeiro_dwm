# 🎨 Padrões de Interface — Sistema Financeiro DWM

Documentação dos padrões visuais e de componentes adotados no projeto.
Sempre consulte este arquivo antes de criar novos elementos de UI.

---

## 🔘 Botões de Ação em Tabelas (Editar / Excluir)

### Padrão Oficial

Todos os botões de ação dentro de células de tabelas (`<td>`) devem seguir
**exatamente** este padrão — sem cor de fundo, sem texto, sem classes Bootstrap,
apenas o emoji como ícone.

```html
<td style="white-space: nowrap; text-align: center;">
    <button onclick="editar(${item.id})"
            style="background: none; border: none; cursor: pointer; font-size: 16px;"
            title="Editar">✏️</button>
    <button onclick="excluir(${item.id})"
            style="background: none; border: none; cursor: pointer; font-size: 16px;"
            title="Excluir">🗑️</button>
</td>
```

### Propriedades obrigatórias

| Propriedade CSS     | Valor          | Motivo                                      |
|---------------------|----------------|---------------------------------------------|
| `background`        | `none`         | Sem cor de fundo                            |
| `border`            | `none`         | Sem borda                                   |
| `cursor`            | `pointer`      | Feedback visual de clicável                 |
| `font-size`         | `16px`         | Tamanho padronizado dos ícones emoji        |
| `white-space` (td)  | `nowrap`       | Impede quebra de linha entre os botões      |
| `text-align` (td)   | `center`       | Centraliza na coluna                        |

### Ícones

| Ação    | Emoji | Atributo `title` |
|---------|-------|------------------|
| Editar  | ✏️    | `"Editar"`       |
| Excluir | 🗑️    | `"Excluir"`      |

### Regras

- ❌ **Não usar** classes Bootstrap (`btn`, `btn-warning`, etc.)
- ❌ **Não usar** texto junto ao ícone ("Editar", "Excluir")
- ❌ **Não usar** cor de fundo ou borda colorida
- ✅ Sempre incluir `title` para acessibilidade (tooltip ao passar o mouse)
- ✅ O `onclick` deve chamar a função correspondente passando o `id` do item

### Referência no código

Implementado em:
- `static/lazy-loader.js` → `renderContaReceber()` e `renderContaPagar()`
- `static/app.js` → fallback `loadContasReceber()` e `loadContasPagar()`
- `static/app.js` → `loadPlanoContas()` (origem do padrão — commit `b157ec3`)

---
*Última atualização: 2026-02-27*
