# Prediction de la revelation depuis une seule entree (2026-10-16)

La sequence originale 1FA7..0ACE est maintenant calculee depuis une seule
capture a 1FA7 : phase CPU/VDP, latch IRQ/IFF, 336 octets RAM et 400 octets
audio. Le modele suit chaque frontiere d'instruction pendant l'effacement
VRAM, la preparation des couleurs, l'attente VBlank, la restauration et
la remise en marche de l'affichage. L'entree de l'attente n'est plus une
donnee observee : elle est produite par le calcul du travail precedent.

Les 24 parcours controles (six passages payants, deux masques d'acteurs,
PAL et NTSC) correspondent exactement a l'execution originale : durees,
phases aux cinq points de controle et tous les horaires d'acceptation IRQ.
Les traces completes restent identiques aux references v0179.
Aux cinq controles, 331 octets RAM et les 400 octets audio correspondent.
Le statut C01B et les entrees C020..C023 ne sont pas compares ; les ports
du controleur sont fixes a zero dans la prediction de l'attente.

7220 contextes synthetiques supplementaires passent : 2520 cas generaux,
3608 autour des acquittements de statut et 1092 autour de l'acquittement
dans le vecteur IRQ. Les routines predites et les banques audio originales
restent intactes ; seuls les appelants et arrets du banc sont modifies.
Les cas isoles utilisent un lecteur audio inactif et des palettes nulles.
Les parcours en jeu exercent le lecteur avec les musiques actives.

Deux details du coeur GPG local sont couverts par des cas positifs :
une lecture de statut qui franchit la ligne physique 192 vers 193 peut
supprimer le VINT attendu ; un VINT qui arrive entre l'acceptation IRQ et
la lecture de statut dans le vecteur peut etre acquitte avec le precedent.
La capture intervient apres la decision IRQ du coeur : la premiere
instruction ne doit pas refaire cette decision. EI bloque l'instruction
suivante. Ces comportements viennent des sources du coeur, pas d'un
ajustement aux durees mesurees.

Limites : mode 4/192 lignes, HINT desactive, VINT actif, pas de NMI/reset
ni d'IRQ imbriquee. Les sorties VRAM et les octets de palette ne sont pas
reconstruits par ce modele. Le chargement avant 1FA7, ses entrees hasard et
historique restent a predire. Aucun delai natif n'est encore integre.
La ROM reste v0183, avec sources natives inchangees. Ceci ne valide ni
la progression complete du jeu, ni le materiel reel.

Reproduire avec les captures locales :

- python tools/build_reveal_phase_core.py
- python tools/validate_reveal_phase_prediction.py
- python tools/validate_reveal_phase_unit.py
- python tools/validate_reveal_phase_unit.py --status-sweep
- python tools/validate_reveal_phase_unit.py --coalescence-sweep
- python tools/archive_reveal_phase_research.py

Modeles, captures, fixtures, sources du coeur et bibliotheque sont conserves
localement dans reveal-phase-research-v0183 avec manifeste SHA-256.
