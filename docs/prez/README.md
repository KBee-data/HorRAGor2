# Support de pitch

`pitch.md` est un deck **Marp** (slides en Markdown) — ~10 slides pour une présentation
d'environ 10 minutes (≈ 1 min/slide).

## Visualiser / exporter

**Dans VS Code (le plus simple)** : installer l'extension *Marp for VS Code*
(`marp-team.marp-vscode`), ouvrir `pitch.md`, puis bouton **aperçu** (en haut à droite).
L'icône d'export permet de sortir un **PDF / PPTX / HTML**.

```bash
code --install-extension marp-team.marp-vscode
```

**En ligne de commande** (si Node dispo) :
```bash
npx @marp-team/marp-cli docs/prez/pitch.md -o docs/prez/pitch.pdf      # PDF
npx @marp-team/marp-cli docs/prez/pitch.md -o docs/prez/pitch.pptx     # PowerPoint
```

## Note sur le brief

Le brief mentionne « **1 à 2 slides maximum** » pour le *support de pitch*. Ce deck couvre la
**présentation complète** (~10 min) demandée ; les **slides 1-2** font office de pitch d'accroche
autonome si le jury attend un support court. À ajuster selon les consignes du jury.

## À personnaliser

- Noms de l'équipe (slide 1).
- Insérer le **schéma d'architecture** (`docs/architecture_globale.mmd`) et le **graphe de
  l'agent** (`uv run horragor-graph`) en images : exporter le Mermaid en SVG/PNG via
  [mermaid.live](https://mermaid.live), puis `![](chemin.svg)` dans le slide voulu.
