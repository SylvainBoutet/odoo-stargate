# Chti Stargate — Odoo 19

Carnet d'adresses Stargate et **ordinateur de numérotation** immersif, sous Odoo 19.

Un module qui démontre qu'Odoo peut tenir les deux bouts : un back-office standard
(listes, formulaires, recherches) **et** une interface immersive reproduisant
l'ordinateur de numérotation de SG‑1, le tout piloté par les mêmes données.

## Fonctionnalités

- **Carnet de destinations** : 36 adresses canoniques (Abydos, Chulak, Tollana…),
  chacune décrite par sa séquence de glyphes (6 coordonnées + point d'origine).
- **Les 39 glyphes de la Voie lactée** : numéro, constellation, forme vectorielle (SVG)
  et image.
- **Journal de composition** : historique des connexions.
- **Ordinateur de numérotation (OWL)** : anneau + 9 chevrons, palette des glyphes,
  composition animée (le symbole s'affiche en grand au centre puis glisse dans sa case),
  ouverture du vortex.
- **Recherches « façon SGC »** : mondes visités / jamais composés, adresses non
  entièrement décodées, extra-galactiques, connexions du jour…

Deux applications : **Stargate** (interface immersive) et **Coordinates** (gestion
standard des tables).

## Installation

Copier le dossier `chti_stargate/` dans un répertoire d'addons Odoo 19, puis :

```bash
odoo-bin -c <conf> -i chti_stargate
```

Interface disponible en français (traductions dans `chti_stargate/i18n/fr.po`).

## Pilotage matériel (à venir)

Le module est conçu pour piloter une réplique physique imprimée en 3D
(anneau WS2812B + chevrons sur ESP32, orchestration HTTP depuis Odoo).

## Crédits

- Formes SVG des glyphes : [Wikimedia Commons — SVG Stargate Milky Way glyphs](https://commons.wikimedia.org/wiki/Category:SVG_Stargate_Milky_Way_glyphs).
- Adresses de portes : référence communautaire [rdanderson.com](https://rdanderson.com/stargate/glyphs/index.htm).

## Avertissement

Projet de fan **non officiel**. *Stargate*, les glyphes et l'univers associé sont la
propriété de MGM. Ce projet est réalisé à but **ludique et démonstratif**, sans lien
officiel ni usage commercial.

## Auteur & licence

CHTI‑TECH — Sylvain Boutet. Distribué sous licence **LGPL‑3** (voir `LICENSE`).
