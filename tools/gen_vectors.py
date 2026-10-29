# PlatformIO-Skript (pre, env:native): drivers/*.json → test/test_drivers/vectors.h.
# Die Testvektoren gelten für den ESP (lib/) und die PC-App (app/studrailmaster/drivers/) gleichermaßen.
# Läuft auch allein: python3 tools/gen_vectors.py
import json
from pathlib import Path

try:
    Import("env")  # noqa: F821
    root = Path(env.subst("$PROJECT_DIR"))  # noqa: F821
except NameError:
    root = Path(__file__).resolve().parent.parent

dst = root / "test" / "test_drivers" / "vectors.h"


def hexbytes(s):
    return ", ".join(f"0x{b:02X}" for b in bytes.fromhex(s))


def ints(values):
    return ", ".join(str(int(v)) for v in values)


jmc = json.loads((root / "drivers" / "jmc.json").read_text(encoding="utf-8"))["vectors"]
mk4 = json.loads((root / "drivers" / "mk4.json").read_text(encoding="utf-8"))["vectors"]
lego = json.loads((root / "drivers" / "lego.json").read_text(encoding="utf-8"))["vectors"]

out = [
    "#pragma once",
    "#include <stdint.h>",
    "",
    "// ERZEUGT von tools/gen_vectors.py aus drivers/*.json – nicht von Hand ändern.",
    "",
    "struct JmcBuild { int8_t dir[4]; uint8_t speed[4]; uint8_t frame[11]; };",
    "static const JmcBuild JMC_BUILD[] = {",
]
for v in jmc["build"]:
    dirs = [c[0] for c in v["cmds"]]
    spds = [c[1] for c in v["cmds"]]
    out.append(f"    {{{{{ints(dirs)}}}, {{{ints(spds)}}}, {{{hexbytes(v['frame'])}}}}},")
out += ["};", "", "struct JmcSpeed { int percent; uint8_t speed; };", "static const JmcSpeed JMC_SPEED[] = {"]
out += [f"    {{{p}, {s}}}," for p, s in jmc["speedFromPercent"]]
out += ["};", "", "struct JmcPercent { int percent[4]; uint8_t frame[11]; };", "static const JmcPercent JMC_PERCENT[] = {"]
out += [f"    {{{{{ints(v['percent'])}}}, {{{hexbytes(v['frame'])}}}}}," for v in jmc["encodePercent"]]
out += ["};", ""]

out += ["struct Mk4Crypt { uint8_t plain[14]; uint8_t len; uint8_t crypt[24]; };", "static const Mk4Crypt MK4_CRYPT[] = {"]
for v in mk4["crypt"]:
    n = len(bytes.fromhex(v["plain"]))
    out.append(f"    {{{{{hexbytes(v['plain'])}}}, {n}, {{{hexbytes(v['crypt'])}}}}},")
out += ["};", "", "struct Mk4Connect { uint8_t ident[3]; uint8_t plain[8]; };", "static const Mk4Connect MK4_CONNECT[] = {"]
out += [f"    {{{{{hexbytes(v['identity'])}}}, {{{hexbytes(v['plain'])}}}}}," for v in mk4["connect"]]
out += ["};", "", "struct Mk4Data { uint8_t ident[3]; int8_t levels[12]; uint8_t plain[10]; };", "static const Mk4Data MK4_DATA[] = {"]
out += [f"    {{{{{hexbytes(v['identity'])}}}, {{{ints(v['levels'])}}}, {{{hexbytes(v['plain'])}}}}}," for v in mk4["data"]]
out += ["};", "", "struct Mk4Level { int percent; int8_t level; };", "static const Mk4Level MK4_LEVEL[] = {"]
out += [f"    {{{p}, {lv}}}," for p, lv in mk4["level"]]
out += ["};", "", "struct Mk4Adv { uint8_t plain[14]; uint8_t len; uint8_t adv[31]; };", "static const Mk4Adv MK4_ADV[] = {"]
for v in mk4["advData"]:
    n = len(bytes.fromhex(v["plain"]))
    out.append(f"    {{{{{hexbytes(v['plain'])}}}, {n}, {{{hexbytes(v['adv'])}}}}},")
out += ["};", ""]

out += ["struct LegoPower { int percent; int8_t power; };", "static const LegoPower LEGO_POWER[] = {"]
out += [f"    {{{p}, {pw}}}," for p, pw in lego["power"]]
out += ["};", "", "struct LegoPercent { int percent[2]; uint8_t frame[16]; };", "static const LegoPercent LEGO_PERCENT[] = {"]
out += [f"    {{{{{ints(v['percent'])}}}, {{{hexbytes(v['frame'])}}}}}," for v in lego["encodePercent"]]
out += ["};", ""]

text = "\n".join(out)
dst.parent.mkdir(parents=True, exist_ok=True)
if not dst.exists() or dst.read_text(encoding="utf-8") != text:
    dst.write_text(text, encoding="utf-8")
    print(f"gen_vectors.py: {dst.relative_to(root)} aktualisiert")
