import sys
import re
from typing import NamedTuple
from sugar import run_sugar

MAX_SCORE = 30


class Piece(NamedTuple):
    kind: str
    height: int
    width: int
    score: int = 0
    amb: int = 0
    touch: list[str] = []


class Game(NamedTuple):
    height: int
    width: int
    pieces: list[Piece]
    goals: list[str] = []


sample = Game(
    3, 1, [
        Piece('R', 1, 1, amb=+1),
        Piece('G', 1, 1, amb=-1),
        Piece('P', 1, 1, touch=['+']),
    ])
large = Game(
    14, 7, [
        Piece('T', 4, 5),
        Piece('G', 3, 2, amb=-1, score=1),
        Piece('G', 3, 2, amb=+1, score=1),
        Piece('G', 4, 1, amb=+1, score=1),
        Piece('G', 3, 3, amb=-2, score=2),
        Piece('B', 4, 1, amb=+1, score=1),
        Piece('B', 3, 2, amb=-1, score=1),
        Piece('B', 4, 2, amb=-2, score=2),
        Piece('R', 1, 4, amb=1, score=1),
        Piece('R', 4, 2, amb=2, score=2),
        Piece('R', 3, 4, amb=2, score=2),
        Piece('P', 2, 4, touch=['+']),
        Piece('P', 4, 3, touch=['G', 'R']),
        Piece('A', 2, 3),
        Piece('A', 4, 3),
    ]
)


def sugar_solver(sample) -> str:
    res = []
    res.extend(var_place(sample))
    res.extend(var_pcount(sample))
    res.extend(var_pcell(sample))
    res.extend(var_adjust(sample))
    res.extend(cond_adjust(sample))
    res.extend(var_sphoto(sample))
    res += ["; GOAL", *sample.goals]
    return "\n".join(res)


def each_cell(sample):
    for y in range(sample.height):
        for x in range(sample.width):
            yield y, x


def var_place(sample) -> list[str]:
    num_pieces = len(sample.pieces)
    res = ["; VAR Place Position", f"(domain d_piece 0 {num_pieces})"]
    for y, x in each_cell(sample):
        res += [f"(int vplace_{y}_{x} d_piece)"]

    res += ["; Cond Count Place"]
    all_vars = " ".join(all_var_place(sample))
    for k in range(1, num_pieces+1):
        res += [f"(count {k} ({all_vars}) eq 1)"]

    res += ["; Cond Piece Inside"]
    for k in range(num_pieces):
        p = sample.pieces[k]
        for y, x in each_cell(sample):
            if y+p.height > sample.height or x+p.width > sample.width:
                res += [f"(!= vplace_{y}_{x} {k+1})"]

    return res


def all_var_place(sample):
    return [f"vplace_{y}_{x}" for y, x in each_cell(sample)]


def var_pcount(sample) -> list[str]:
    res = ["; VAR Piece Count"]
    for y, x in each_cell(sample):
        res += [f"(int vcount_{y}_{x} 0 1)"]

    put = put_piece(sample)
    res += ["; Cond Count Piece"]
    for y, x in each_cell(sample):
        counts = [
            f"(if (= vplace_{oy}_{ox} {i}) 1 0)"
            for i, oy, ox in put[y][x]
        ]
        res += [f"(= vcount_{y}_{x} (+ {" ".join(counts)}))"]
    return res


def put_piece(sample):
    put = [[[] for _ in range(sample.width)] for _ in range(sample.height)]
    for i, p in enumerate(sample.pieces):
        for y, x in each_cell(sample):
            for dy in range(p.height):
                for dx in range(p.width):
                    if y+dy >= sample.height or x+dx >= sample.width:
                        continue
                    put[y+dy][x+dx].append((i+1, y, x))
    return put


def var_pcell(sample):
    res = ["; VAR Piece Cell"]
    for y, x in each_cell(sample):
        res += [f"(int vpcell_{y}_{x} d_piece)"]

    put = put_piece(sample)
    res += ["; Cond Piece Cell"]
    for y, x in each_cell(sample):
        cells = [
            f"(if (= vplace_{oy}_{ox} {i}) {i} 0)"
            for i, oy, ox in put[y][x]
        ]
        res += [f"(= vpcell_{y}_{x} (+ {' '.join(cells)}))"]
    return res


def var_adjust(sample):
    res = ["; VAR Adjust"]
    for i in range(len(sample.pieces)):
        for j in range(i+1, len(sample.pieces)):
            res += [f"(bool vadjust_{i+1}_{j+1})"]

    res += ["; Cond Adjust"]

    def cell_str(y, x, dy, dx, i, j):
        return f"(and (= vpcell_{y}_{x} {i+1}) (= vpcell_{y+dy}_{x+dx} {j+1}))"
    for i in range(len(sample.pieces)):
        for j in range(i+1, len(sample.pieces)):
            cell = []
            for y in range(sample.height):
                for x in range(sample.width-1):
                    cell.append(cell_str(y, x, 0, 1, i, j))
                    cell.append(cell_str(y, x, 0, 1, j, i))
            for x in range(sample.width):
                for y in range(sample.height-1):
                    cell.append(cell_str(y, x, 1, 0, i, j))
                    cell.append(cell_str(y, x, 1, 0, j, i))
            res += [f"(iff vadjust_{i+1}_{j+1} (or {' '.join(cell)}))"]
    return res


def cond_adjust(sample):
    res = ["; Cond Adjust Count"]
    for i in range(len(sample.pieces)):
        for j in range(i+1, len(sample.pieces)):
            if sample.pieces[i].kind == sample.pieces[j].kind:
                res += [f"(not vadjust_{i+1}_{j+1})"]
    return res


def var_sphoto(sample):
    res = ["; VAR Photo Score"]
    vars = []
    for i, piece in enumerate(sample.pieces):
        if piece.kind != "P":
            continue
        for j, other in enumerate(sample.pieces):
            if i == j:
                continue
            amb_check = "+" in piece.touch and other.amb > 0
            amb_check |= "-" in piece.touch and other.amb < 0
            if other.kind in piece.touch or amb_check:
                oi, oj = min(i, j), max(i, j)
                vars.append(f"(if vadjust_{oi+1}_{oj+1} 1 0)")
    res += [f"(int v_sphoto 0 {MAX_SCORE})"]
    res += [f"(= v_sphoto (+ {' '.join(vars)}))"]
    return res


def collect_metrics(game):
    piece_areas = [p.height * p.width for p in game.pieces]
    art_score = sum(p.score for p in game.pieces)
    amb_score = sum(p.amb for p in game.pieces)
    pieces_cnt = {c: sum(1 for p in game.pieces if p.kind == c)
                  for c in ["R", "G", "B", "P", "A", "T"]}
    return {
        "area": game.height * game.width,
        "piece_count": len(game.pieces),
        "piece_areas": sum(piece_areas),
        "rest": game.height * game.width - sum(piece_areas),
        "art_score": art_score,
        "amb_score": amb_score,
        "pieces": pieces_cnt,
    }


def is_forced(p):
    return p.kind == "A" or p.kind == "T"


def get_piece_subgame(game):
    ads = [(i, p) for i, p in enumerate(game.pieces) if is_forced(p)]
    ad_size = sum(p.height * p.width for _, p in ads)
    others = [(i, p.height * p.width)
              for i, p in enumerate(game.pieces) if not is_forced(p)]
    rest_size = game.height * game.width - ad_size
    subsizes = collect_subsizes(rest_size, others)
    return [
        game._replace(pieces=[game.pieces[i] for i, _ in [*subs, *ads]])
        for subs in subsizes
    ]


def collect_subsizes(rest_size, subs):
    kicks = sum(p[1] for p in subs) - rest_size
    index = calc_subsizes(kicks, [p[1] for p in subs])
    return [
        [subs[i] for i, _ in enumerate(subs) if i not in ind]
        for ind in index
    ]


def calc_subsizes(total, areas, use=4):
    ind_areas = list(sorted(((i, a)
                     for i, a in enumerate(areas)), key=lambda x: -x[1]))
    res = []
    prev = [([], 0)]  # (index, total)
    for (a, area) in ind_areas:
        next = [([], 0)]
        for ind, t in [*prev]:
            if t + area < total:
                if len(ind) < use - 1:
                    next.append(([*ind, a], t + area))
                    next.append((ind, t))
            else:
                res.append([*ind, a])
        prev = next
    return res


def piece_str(piece):
    return f"{piece.kind}{piece.height}x{piece.width} {piece.score} {piece.amb} {piece.touch}"


def same_pieces(l1, l2):
    def norm(l):
        return sorted(piece_str(p) for p in l)
    return all(p1 == p2 for p1, p2 in zip(norm(l1), norm(l2)))


def remove_dup_games(games):
    res = []
    for g in games:
        for r in res:
            if same_pieces(g.pieces, r.pieces):
                break
        else:
            res.append(g)
    return res


def test_collect_subsizes():
    subs = get_piece_subgame(large)
    subs = remove_dup_games(subs)
    use = []
    for sub in subs:
        if not (expect_score(sub) >= 14):
            continue
        use.append(sub)
    return use


def expect_score(game):
    met = collect_metrics(game)
    rest_score = [3, 3, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0]
    res = met["art_score"] - abs(met["amb_score"]) + rest_score[met["rest"]]
    res += min(met["pieces"][c] for c in ["R", "G", "B"])  # T Score
    return res


def set_goal(game):
    score = expect_score(game)
    target = 19
    return game._replace(goals=[f"(= v_sphoto {target - score})"])


def peek_line(lines, key):
    res = []
    for l in lines:
        m = re.match(r"a ("+key+r")\s+(\S+)", l)
        if m is None:
            continue
        res.append((m.group(1), parse_let(m.group(2))))
    return res


def parse_let(s):
    if s == "false":
        return "F"
    if s == "true":
        return "T"
    return int(s)


def peek_file(lines, key):
    res = []
    for l in lines:
        m = re.match(r"a "+key+r"_(\d+)_(\d+)\s+(\S+)", l)
        if m is None:
            continue
        res.append((int(m.group(1)), int(m.group(2)), parse_let(m.group(3))))
    return res


def peek_table(lines, key, h, w):
    res = [[None]*w for _ in range(h)]
    for y, x, a in peek_file(lines, key):
        res[y][x] = a
    return res


def parse_result(game, lines):
    if lines[0] != "s SATISFIABLE":
        print("unsolvable")
        return False

    def print_key(key):
        print(key)
        print_table(peek_table(lines, key, game.height, game.width))

    def print_board():
        print("board")
        table = peek_table(lines, "vpcell", game.height, game.width)
        colors = [[game.pieces[c-1].kind if c is not None and c >
                   0 else "." for c in row] for row in table]
        print_table(colors)
    print_key("vplace")
    print_key("vcount")
    print_key("vpcell")
    print(peek_line(lines, "v_sphoto"))
    print_table(peek_table(lines, "vadjust", len(
        game.pieces)+1, len(game.pieces)+1))
    print_board()
    return True


def print_table(table):
    for row in table:
        print(" ".join(str(x) for x in row))


if __name__ == '__main__':
    use = test_collect_subsizes()
    use = [use[4], use[7]]
    for i, u in enumerate(use):
        to_solve = set_goal(u)
        csp = sugar_solver(to_solve)
        print(f"#{i}/{len(use)}", collect_metrics(to_solve), to_solve.goals)
        res = run_sugar(csp).split("\n")
        print("solved: ", "\n".join(res))
        parse_result(to_solve, res)
