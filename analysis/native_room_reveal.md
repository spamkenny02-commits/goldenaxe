# Rallumage et fondu natifs - 24 octobre 2026

La chaine continue qui commencait en 16D0 atteint maintenant la premiere attente
0B95 du contour, apres le fondu. Aucune horloge, graine, palette, initialisation
du heros ou commande musicale intermediaire n'est injectee.

`source_room_reveal_prepare` traduit 1FA7..0ACE : effacement des 768 mots
3800..3DFF, sauvegarde de la palette cible DCC0, noir dans DCA0, attente complete
0B95 et restauration du registre d'affichage. Le nombre de tuiles du bitmap du
heros en attente est lu dans son descripteur ROM avant l'IRQ complete.
Le miroir VRAM optionnel recoit l'effacement du premier plan uniquement.

`source_room_reveal_fade` traduit 0ACE..0B09 : composantes bleu/vert/rouge,
comparaison des 32 couleurs et deux attentes completes pour chaque pas modifie.
La palette et l'audio restent vivants pendant ces interruptions. Le RET aboutit
a la frontiere prefetchee 1FB6. Le banc execute ensuite les 55 T/5 M1 originaux
jusqu'au premier0B95 du contour, pour comparer aussi l'etat complet apres le fondu.

Validation :

- 24 parcours source, six destinations exterieures ordinaires, masques00/FF,
  NTSC/PAL.1 032 points comparent phase, temps, M1/R,331 octets RAM et400 audio,
  ainsi que tous les decalages des IRQ.24 retours1FB6 comparent temps/C02F.
  Heros475, acteurs, scripts, historique, masques, graphismes d'ennemis et les
  palettes cibles sont conserves dans les comparaisons. Les changements de palette
  aboutissent aux composantes6bits de la cible SMS.
- 48 executions de cette chaine compilee pour68000 passent,24 par region physique.
- 96 cas de fondu compares au code Z80 original : palettes egales, montantes,
  descendantes, mixtes et bits hauts, saut palette, compensation et retard d'entree.
  Les palettes64, RAM331, audio400, temps/M1/R sont controles.
- 192 executions compilees68000 du fondu passent,96 par region physique.

Les cartouches de diagnostic desactivent les IRQ physiques MD tout en executant
l'horloge virtuelle, les IRQ SMS natives et le lecteur audio natif. Leur duree
d'execution ne mesure pas la cadence du jeu. Les autres octets du corps RAM et
du miroir compares en68000 n'ont qu'une preuve de concordance avec l'hote.

La chaine reste hors du chemin jouable. Depuis le raccordement source_irq_video,
les IRQ publient aussi leurs transferts dans les miroirs VRAM/SAT/CRAM.
Les contours, le raccordement SGDK, l'origine globale de l'horloge, les autres
classes de carte et la campagne complete restent ouverts. Aucune nouvelle ROM
jouable n'est annoncee : les275 versions et la v0275 sont preservees.

Rapports : native_room_reveal_report.json, native_room_reveal_68k_report.json,
native_room_fade_report.json et native_room_fade_68k_report.json.

Update2026-10-24: source_irq_video is now bound to the continuous loader.
Its native IRQ mirrors cover SAT,hero bitmap,HUD,CRAM,scroll/line registers
and ROM/SRAM/row queues.24 source chains and48 compiled68000 chains pass
with video delivery active; other mirror bytes remain host-parity evidence.
Physical SGDK publication/pacing and contours are still external.
See native_irq_video.md for the separate288 source/576 native video cases.
