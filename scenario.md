# Parcourir un trajet en respectant les panneaux routiers, avec des pièges et des zones à risque. Le joueur doit éviter les pénalités et optimiser son temps.

- Stop (obligation de s’arrêter N secondes).
- Cédez le passage (ralentir à 30% de la vitesse).
- Limitation de vitesse à 30 km/h (vitesse réduite).
- Passage piétons (obligation de s’arrêter si un "piéton" est présent).
- Priorité à droite (simulée par un autre robot ou un obstacle).
- Interdiction de stationner (zone à éviter).
- Sens giratoire (obligation de tourner dans le sens indiqué).


       [Départ]
              |
              v
       [Limite 30] --> [Passage piétons] --> [Cédez le passage]
              |                              |
              v                              v
       [Sens giratoire] <-- [Priorité à droite] <-- [Interdiction de stationner]
              |
              v
       [Stop] --> [Arrivée]


## Détails des Étapes :


### Départ :

Le joueur démarre son robot et accélère progressivement.


### Limite de vitesse à 30 km/h :

Le robot doit ralentir (vitesse réduite dans le code).
Pénalité : Si le robot dépasse la vitesse, +2 secondes.


### Passage piétons :

Un "piéton" (figurine) est placé aléatoirement.
Règle : Le robot doit s’arrêter si un piéton est présent.
Pénalité : +5 secondes si le robot ne s’arrête pas.


### Cédez le passage :

Le robot doit ralentir (vitesse réduite).
Pénalité : +3 secondes si le robot ne ralentit pas.


### Priorité à droite :

Un obstacle (ex: autre robot ou voiture miniature) arrive de la droite.
Règle : Le robot doit laisser passer l’obstacle.
Pénalité : +4 secondes en cas de collision.


### Interdiction de stationner :

Zone délimitée où le robot ne doit pas s’arrêter.
Pénalité : +3 secondes si le robot s’arrête dans cette zone.


### Sens giratoire :

Le robot doit tourner dans le sens indiqué (flèches dessinées).
Pénalité : +5 secondes si le robot tourne dans le mauvais sens.


### Stop :

Le robot doit s’arrêter complètement pendant 3 secondes.
Pénalité : +5 secondes si le robot ne s’arrête pas.


### Arrivée :

Le chronomètre s’arrête. Le joueur gagne s’il n’a pas accumulé trop de pénalités !

## Règles du Jeu
### But :

- Parcourir le trajet le plus rapidement possible en respectant les panneaux.
- Éviter les pénalités pour obtenir le meilleur score.

### Système de Score :

- Temps de base : Temps mis pour parcourir le trajet.
- Pénalités : Ajoutées au temps de base (voir ci-dessus).
- Bonus : -2 secondes si aucun panneau n’est violé.
