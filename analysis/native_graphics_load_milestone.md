# Chargement graphique natif 16D0..24B9

Le chemin audite de changement de graphismes exterieurs class0 couvre
maintenant 16D0..24B9 avec une seule horloge native et le meme contexte
d'interruption/audio. La traduction comprend le prefixe 032A, le decodeur
RAM0C00 a deux/quatre plans, les sauvegardes C080, la restauration des
metatuiles animees, les sept metatuiles supplementaires et leurs attributs,
le terrain D100, puis la copie 1024 octets vers la SRAM.

Chaque instruction avance SourceClock ; DI/EI et les doubles lectures M1
des instructions ED/CB sont conserves. Les six points 1706,170E,1720,1733,
1748,24B9 partagent la meme phase et le meme etat : aucune reinitialisation
ni injection intermediaire. Le travail de premier plan est de 982060 T et
137614 M1 ; les interruptions audio et la duree totale restent dynamiques.

Les 24 parcours controles disponibles retrouvent a chacun des six points
la duree, la phase raster, R/M1, 331 octets RAM et 400 octets audio de la SMS,
ainsi que tous les instants d'acceptation des interruptions. Les 24 vecteurs
passent egalement sur code 68000 compile en PAL et NTSC, zero echec.
Les autres details du journal et les cinq octets exclus du comparatif SMS
sont controles par parite avec l'hote dans le noyau compile.

Une nouvelle instrumentation source lit uniquement les donnees graphiques.
Les anciens snapshots de phase restent identiques, ainsi que R et les
deltas M1. Les hashes FNV32 des donnees source sont compares directement
aux sorties natives sur les 24 parcours : 6176 octets de motifs, 912 octets
de metatuiles de base plus 56 supplementaires, 16 octets de sauvegarde,
512 octets de terrain decode et512 premiers octets copies en SRAM.

Les zones non reecrites ne sont pas supposees nulles. Le decodeur terrain
n'ecrit que 512 octets, alors que la copie SRAM en transporte 1024. L'API
recoit donc des tampons appartenant au caller et conserve les autres octets.
Le controle natif utilise une sentinelle pour ces zones et verifie aussi
la copie complete 1024 octets ; la capture source n'affirme pas verifier
les octets anterieurs non initialises par ce chemin.

Reproduction :

- `python tools/build_graphics_data_core.py`
- `python tools/validate_graphics_source_data.py`
- `python tools/validate_native_graphics_load.py`
- `python tools/validate_native_graphics_load_68k.py`

L'observateur utilise la ROM SMS originale avec les mises en situation
controlees deja archivees. Il est compile dans une DLL distincte ; le
fichier source du coeur est restaure apres compilation. Ce controle ne
constitue pas une partie naturelle complete.

Le raccordement au jeu reste ouvert. Cette API traite uniquement class0,
changement de banque, affichage coupe et C0AC=0. Les entrees de phase restent
observees ; le demarrage, les autres classes et la suite cartes/HUD/acteurs
doivent transmettre leur propre etat logique avant activation globale.
Les uploads physiques VDP et le mapper ne sont pas emules par cette API.
La recompilation du jeu conserve les octets exacts de la ROM v0198.
