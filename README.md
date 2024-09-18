# fit2print-solver

```
$ rye run main
#0/2 {'area': 98, 'piece_count': 11, 'piece_areas': 97, 'rest': 1, 'art_score': 10, 'amb_score': 0, 'pieces': {'R': 2, 'G': 3, 'B': 2, 'P': 1, 'A': 2, 'T': 1}} ['(= v_sphoto 4)']
solved:  s SATISFIABLE
board
A A A B G G G
A A A B G G G
A A A B G G G
A A A B P P P
R R R R P P P
G A A A P P P
G A A A P P P
G R R R R G G
G R R R R G G
. R R R R G G
B B T T T T T
B B T T T T T
B B T T T T T
B B T T T T T
```

## 変数と制約

- 自由変数 パーツ配列変数 (HxW)

  - 与えられたパーツが 1 回ずつ、残りは 0 で埋まる

- パーツ配置回数変数

  - パーツが置かれた回数を持つ
  - 1 以下である必要がある。1 のマスで配置マス変数を求める

- パーツ配置マス変数

  - 与えられたパーツで塗るようにする
  - パーツ配列変数から形を参照して塗る制約を貼る

- 独立余白マス ID 変数
- 余白マス集計変数

- 隣接性変数 (PxP/2)

  - パーツ同士が隣接しているなら True になる

- 記事スコア変数
- 写真スコア変数
- 雰囲気スコア変数
- 連結空白マス数変数

- 集計変数
