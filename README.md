# Sur les épaules de Darwin — catalogue des émissions

Petit site statique pour explorer, trier et rechercher les émissions de
*Sur les épaules de Darwin* (Jean Claude Ameisen, France Inter, septembre 2010 –
juin 2022), l'interface de radiofrance.fr n'étant pas pratique pour ça.

L'émission est arrêtée : les données sont extraites **une seule fois** et
commitées. Il n'y a pas de mise à jour à gérer.

## Choix techniques

- **Pas de framework, pas de build** : `index.html` + `app.js` + `data/episodes.json`.
  Les bibliothèques sont chargées depuis un CDN. Le site doit pouvoir tourner
  tel quel dans 10 ans. Astro a été écarté : une seule page, rien à générer.
- **Tableau** triable et filtrable : [Tabulator](https://tabulator.info) (ou équivalent).
- **Recherche plein texte** côté navigateur : [MiniSearch](https://lucaong.github.io/minisearch/).
  Pagefind a été écarté : surdimensionné pour ~340 émissions (1,4 Mo de JSON).
- **Hébergement** : GitHub Pages (`https://<user>.github.io/<repo>/`).
  Le site est servi dans un sous-chemin : utiliser des chemins relatifs (`./data/episodes.json`).
- Test local : `python3 -m http.server`.

Le critère de qualité qui intéresse le plus : **le nombre de rediffusions**
(`rerunCount`), plus une émission a été rediffusée, meilleure elle est.

## Données

```
data/
  episodes.json           le fichier consommé par le site
  topics.json             sujets générés par LLM, par id d'émission
  wikipedia.txt           wikitext de la page Wikipédia (source)
  radiofrance-pages.json  métadonnées des 596 pages radiofrance.fr (source)
raw/                      ignoré par git
  radiofrance-pages.tar.gz  cache HTML des pages radiofrance.fr (25 Mo)
  rf.json                   sortie brute du crawl
scripts/
  crawl.py    liste et télécharge les pages radiofrance.fr (utilise le cache)
  compare.py  croise Wikipédia et radiofrance.fr, affiche les écarts
  body.py     extraction du corps HTML des pages
  build.py    produit data/episodes.json
```

Pour reconstruire : `python3 scripts/build.py` depuis la racine. Le cache est
décompressé automatiquement dans `raw/cache/` si besoin (il faut donc garder
l'archive dans `raw/`, qui n'est pas versionné).

### Sources

- **Wikipédia** ([page](https://fr.wikipedia.org/wiki/Sur_les_%C3%A9paules_de_Darwin)) :
  tableau des 607 diffusions (n° de diffusion, n° d'émission, titre, date, teasing).
  C'est la colonne vertébrale : liste des diffusions et rattachement des
  rediffusions à leur émission originale.
- **radiofrance.fr** ([page](https://www.radiofrance.fr/franceinter/podcasts/sur-les-epaules-de-darwin),
  30 pages de liste `?p=N`) : une page par diffusion. Le bloc JSON-LD
  `RadioEpisode` donne titre, date, MP3, durée, image ; le HTML donne intro et
  citations, articles scientifiques, livres, chansons, liens, thèmes, équipe.
- Le **flux RSS** cité par Wikipédia (`rss_11549.xml`) est mort (404).

### Corrections appliquées à Wikipédia

Wikipédia a été vérifié contre radiofrance.fr (dates, titres, et les pages de
rediffusion qui citent la date de l'original). Corrections dans `build.py` :

- Dates (`DATE_FIX`) : diffusions n° 118 et 119 → 1er et 8 déc. 2012 (et non
  novembre) ; n° 279 → 30 janv. 2016 (et non le 31).
- Rattachements (`EP_FIX`) : diffusion n° 518 « La tectonique des plaques » →
  émission n° 191 (et non 40) ; n° 531 « Habiter notre corps » → émission n° 95
  (et non 131).
- Les marqueurs R1/R2… de Wikipédia sont incohérents (doublons, trous) : ils
  sont ignorés, `rerun` et `rerunCount` sont recalculés en comptant les diffusions.

Cas vérifiés où Wikipédia a raison : « Visages » du 17 avril 2021 (la page
radiofrance.fr cite une mauvaise date d'original) ; « Oliver Sacks » du
24 déc. 2016 est bien la partie 2 (vérifié à l'écoute).

Non vérifiables : 12 rediffusions n'ont pas de page radiofrance.fr (dont les
8 « Aux origines du chocolat » de 2019-2020). La page « Mouvement de grève »
du 4 avril 2015 est ignorée (pas d'émission).

### Format de `episodes.json`

```jsonc
{
  "generatedAt": "2026-09-25",
  "sources": { "wikipedia": "…", "radiofrance": "…" },
  "episodes": [
    {
      "id": 142,                          // n° d'émission (Wikipédia)
      "title": "Argile du passé (1)",     // titre Wikipédia
      "series": { "name": "Argile du passé", "part": 1 },  // null si hors série
      "firstBroadcast": "2014-09-06",
      "rerunCount": 0,
      "durationSeconds": 3232,
      "audioUrl": "https://media.radiofrance-podcast.net/…mp3",
      "pageUrl": "https://www.radiofrance.fr/…",
      "imageUrl": "…",
      "teaser": null,                     // colonne « Teasing » de Wikipédia
      "standfirst": "Argile du passé",    // chapeau radiofrance.fr
      "intro": "Argile du passé que l'aujourd'hui…",  // texte d'intro, citations incluses
      "articles": ["Higham T, … Nature 2014, 512:306-9."],
      "books": ["Svante Pääbo. Neanderthal Man… Basic Books, 2014."],
      "songs": ["River par Ibeyi (XL Recordings)"],
      "links": [{ "text": "…", "url": "…" }],
      "films": [{ "text": "…" }],
      "themes": ["Mythologie", "Sciences et Savoirs"],   // thèmes radiofrance.fr
      "topics": ["disparition de Néandertal", "Dénisovien", "Jorge Luis Borges"],
      "team": [{ "name": "Christophe Imbert", "role": "Réalisation" }],
      "broadcasts": [{ "number": 209, "date": "2014-09-06", "rerun": 0 }]
    }
  ]
}
```

Le contenu (MP3, intro, références) vient de la page de la diffusion originale,
ou de la page de diffusion la plus riche quand celle de l'original est vide.

### Limites connues

- `articles`, `books`, `songs` sont des **lignes de texte**, pas des objets
  structurés : les formats varient trop sur 12 ans pour un découpage fiable par
  heuristique (≈ 25 % d'erreurs sur les chansons). Suffisant pour la recherche
  plein texte ; un découpage fin demanderait une passe LLM.
- `topics` (5 par émission en général, de 1 à 8) a été généré une fois par LLM à partir du titre,
  de l'intro et des références. Très spécifique : 1 032 sujets distincts pour
  1 590 occurrences. Bien pour la recherche, trop fin pour un filtre en liste ;
  une passe de regroupement vers ~100 sujets larges serait nécessaire pour ça.
- Une émission n'a pas de MP3.

## Prochaine étape

Écrire le site : tableau (titre, série, date, durée, rediffusions, sujets),
tri par colonne, filtres (série, année, thème), recherche plein texte sur
titre, intro, sujets et références, lien vers la page radiofrance.fr et
lecture du MP3.
