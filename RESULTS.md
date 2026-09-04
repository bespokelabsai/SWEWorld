# g2 world arm

Ended 2026-09-02T16:25:06Z

## Result

- reknit + gates: see audit
- inject: clean
- world arm built
- boot + oracle validation exit: 0  (0 = world booted, setup.sh ingested the plant, oracle scored 1.0)

### Audit
```
  unknit           clean
  double_booked    22
       g2.r1.l-kept-konrad: konrad speaks in #code-review at 13:19 on 2025-03-20, but the corpus has them in #co
       g2.r1.l-kept-konrad: konrad speaks in #code-review at 13:19 on 2025-03-20, but the corpus has them in #co
       g2.r1.l-kept-nils: dermot speaks in #engineering at 11:53 on 2025-03-19, but the corpus has them in #rele
  voice_problems   clean
  stock_phrasing   2
       3 exchanges END with words used nowhere else: 'best we can do' (g2.r1.herring-marker-inside-budget-dario,
       3 exchanges END with words used nowhere else: 'i had it filed' (g2.r1.l-off-konrad, g2.r1.l-seam-dermot, 
  too_wordy        42
       g2.r1.l-kept-gideon: the exchange is 8.8x the remark (146 chars over 7 turns) — inflated rather than spre
       g2.r1.l-kept-konrad: the exchange is 9.5x the remark (134 chars over 7 turns) — inflated rather than spre
       g2.r1.l-kept-nils: the exchange is 11.0x the remark (129 chars over 7 turns) — inflated rather than sprea
  uncarried        clean
  identifiers      clean
```

### Next
1. measure: cli.py trial executor-output-cap --arm world --job world-g2-1
2. README with the MuSR tree and the fragmented conversations
